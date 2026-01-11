from typing import List, Dict, Optional
from datetime import date, datetime

from Persistencia.Impl import ContratoKitnetImpl, PagamentoAluguelImpl, KitnetImpl, InquilinoImpl

from Persistencia.Entidades import ContratoKitnet, PagamentoAluguel

from Service import FinanceiroService

class LocacaoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_contrato = ContratoKitnetImpl()
        self.dao_pagamento = PagamentoAluguelImpl()
        self.dao_kitnet = KitnetImpl()
        self.dao_inquilino = InquilinoImpl()
        # Injeção ou Instanciação
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def alugar(self, id_kitnet: int, id_inquilino: int, valor_aluguel: float, dia_vencimento: int, 
               data_inicio: str, valor_esgoto: float = 0.0, data_fim: str = None, 
               mobiliado: int = 0, obs: str = "") -> str:
        
        # 1. Verifica disponibilidade
        kitnet = self.dao_kitnet.buscar_por_id(id_kitnet)
        if kitnet.status != 'LIVRE': 
            return "Erro: Kitnet já ocupada."

        # 2. Cria o contrato
        novo_contrato = ContratoKitnet(
            id_kitnet=id_kitnet, 
            id_inquilino=id_inquilino, 
            valor_fechado=valor_aluguel,
            valor_esgoto_padrao=valor_esgoto, # <--- Novo campo salvo no contrato
            data_vencimento=dia_vencimento, 
            data_inicio=data_inicio, 
            data_fim=data_fim,
            ativo=1,
            mobiliado=mobiliado,
            obs_mobiliado=obs,
            pdf_caminho_contrato_kit=None 
        )
        
        id_gerado = self.dao_contrato.salvar(novo_contrato)
        
        if id_gerado:
            # 3. Atualiza Status da Kitnet para OCUPADA
            kitnet.status = 'OCUPADA'
            self.dao_kitnet.atualizar(kitnet)

            # 4. Gera a primeira cobrança (Boleto interno)
            mes_atual = str(data_inicio)[:7] # Ex: '2026-01'
            valor_total_mes = valor_aluguel + valor_esgoto
            self._criar_cobranca(id_gerado, mes_atual, valor_total_mes)
            
            return "Sucesso: Contrato fechado e Kitnet alugada!"
        return "Erro ao gerar contrato."

    def processar_pagamento_aluguel(self, id_pagamento: int, valor_recebido: float, banco: str, 
                                    eh_quitacao_com_desconto: bool = False, obs: str = "") -> str:
        """
        Lógica Central de Recebimento:
        - Aceita parcial (mantém dívida aberta)
        - Aceita quitação com desconto (fecha a dívida no valor pago)
        """
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Pagamento não encontrado."
        
        # Se já estava 'pago' (total), não deixa pagar de novo, mas se for 'parcial' deixa continuar.
        if pag.status == 'pago': return "Erro: Este mês já está quitado."

        # Valores atuais no banco
        ja_pago = pag.valor_pago or 0.0
        divida_total = pag.valor_esperado
        
        novo_valor_pago_acumulado = ja_pago + valor_recebido
        novo_status = 'pendente'
        msg_retorno = ""

        # --- LÓGICA DE STATUS E SALDO ---
        if eh_quitacao_com_desconto:
            # CASO: Acordo/Dificuldade -> O valor esperado vira o que foi pago
            pag.valor_esperado = novo_valor_pago_acumulado
            pag.status = 'pago'
            novo_status = 'pago'
            msg_retorno = "Sucesso: Dívida quitada com desconto/ajuste."
        else:
            # CASO NORMAL
            if novo_valor_pago_acumulado >= (divida_total - 0.05): # Margem de centavos
                pag.status = 'pago'
                novo_status = 'pago'
                msg_retorno = "Sucesso: Pagamento concluído."
            else:
                pag.status = 'parcial'
                novo_status = 'parcial'
                restante = divida_total - novo_valor_pago_acumulado
                msg_retorno = f"Sucesso: Pagamento PARCIAL registrado. Restam R$ {restante:.2f}"

        # 1. Atualiza no Banco de Dados
        pag.valor_pago = novo_valor_pago_acumulado
        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        
        # Adiciona observação se houver
        if obs:
            pag.obs = (pag.obs or "") + " | " + obs
            
        self.dao_pagamento.atualizar(pag)

        # 2. Integração Financeira (Lança Receita)
        # Importante: Lança apenas o valor que ENTROU AGORA (valor_recebido), não o acumulado
        contrato = self.dao_contrato.buscar_por_id(pag.id_contrato_kitnet)
        kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
        inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
        
        identificacao = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "?"
        nome_inq = inquilino.nome if inquilino else "?"
        
        desc_lancamento = f"Aluguel {identificacao} ({nome_inq}) - Ref: {pag.mes_referencia}"
        if novo_status == 'parcial':
            desc_lancamento += " [PARCIAL]"
        if eh_quitacao_com_desconto:
            desc_lancamento += " [ACORDO]"

        self.fin_service.registrar_receita_manual(
            descricao=desc_lancamento, 
            valor=valor_recebido, 
            id_categoria=1, # 1 deve ser o ID da Categoria 'Aluguel'
            data=pag.data_pagamento, 
            banco=banco, 
            forma="Transferência/Pix", # Pode virar param se quiser
            id_kitnet=kitnet.id_kitnet if kitnet else None,
            id_pagamento_aluguel=pag.id_aluguel
        )
        
        return msg_retorno

    def gerar_cobrancas_mensais(self) -> str:
        """
        Roda todo mês: Gera boleto para quem ainda não tem no mês atual.
        Soma Aluguel + Esgoto.
        """
        contratos = self.dao_contrato.listar_ativos()
        todos_pags = self.dao_pagamento.listar_todos()
        mes_atual = date.today().strftime("%Y-%m") # Ex: 2026-01
        count = 0

        for c in contratos:
            # Verifica se já existe pagamento para este contrato neste mês
            ja_existe = any(p.id_contrato_kitnet == c.id_contrato_kitnet and p.mes_referencia == mes_atual for p in todos_pags)
            
            if not ja_existe:
                # SOMA INTELIGENTE: Aluguel + Esgoto
                valor_total = c.valor_fechado + (c.valor_esgoto_padrao or 0.0)
                self._criar_cobranca(c.id_contrato_kitnet, mes_atual, valor_total)
                count += 1
        
        return f"Processamento concluído. {count} novas cobranças geradas para {mes_atual}."

    def encerrar_contrato(self, id_contrato: int, data_saida: str) -> str:
        """Finaliza o contrato e libera a kitnet"""
        contrato = self.dao_contrato.buscar_por_id(id_contrato)
        if not contrato: return "Contrato não encontrado."
        
        # 1. Desativa contrato
        contrato.ativo = 0
        contrato.data_fim = data_saida
        self.dao_contrato.salvar(contrato)
        
        # 2. Libera Kitnet
        kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
        if kitnet:
            kitnet.status = 'LIVRE'
            self.dao_kitnet.salvar(kitnet)
            
        return "Contrato encerrado e Kitnet liberada."

    # --- MÉTODOS AUXILIARES ---

    def _criar_cobranca(self, id_contrato, mes_ref, valor_total_esperado):
        # Cria o registro na tabela de pagamentos com o valor esperado total
        novo_pag = PagamentoAluguel(
            id_contrato_kitnet=id_contrato, 
            mes_referencia=mes_ref,
            valor_esperado=valor_total_esperado, # Valor cheio
            valor_pago=0.0, 
            status='pendente', 
            data_pagamento=None,
            obs=""
        )
        self.dao_pagamento.salvar(novo_pag)

    def listar_alugueis_pendentes(self) -> List[Dict]:
        """
        Retorna lista formatada para a tela de Recebimentos.
        Inclui pendentes e parciais.
        """
        pendentes = self.dao_pagamento.listar_pendentes() # O DAO já filtra (pendente + parcial)
        resultado = []
        
        for p in pendentes:
            contrato = self.dao_contrato.buscar_por_id(p.id_contrato_kitnet)
            if not contrato: continue
            
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
            
            nome_kit = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "???"
            nome_inq = inquilino.nome if inquilino else "???"
            
            # Cálculo crucial para a interface
            restante = p.valor_esperado - p.valor_pago
            
            # Monta objeto para o front-end
            resultado.append({
                "id_pagamento": p.id_aluguel,
                # Label bonita para o SelectBox
                "label_combo": f"{nome_kit} - {nome_inq} ({p.mes_referencia}) - Falta: R$ {restante:.2f}",
                "descricao_detalhada": f"{nome_kit} - {nome_inq}",
                "mes": p.mes_referencia,
                "valor_total_esperado": p.valor_esperado, 
                "valor_ja_pago": p.valor_pago,
                "valor_restante": restante,
                "vencimento_dia": contrato.data_vencimento,
                "status": p.status
            })
        return resultado