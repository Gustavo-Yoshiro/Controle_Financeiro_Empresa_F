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
            valor_esgoto_padrao=valor_esgoto,
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
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Pagamento não encontrado."
        
        if pag.status == 'pago': return "Erro: Este mês já está quitado."

        ja_pago = pag.valor_pago or 0.0
        divida_total = pag.valor_esperado
        
        novo_valor_pago_acumulado = ja_pago + valor_recebido
        novo_status = 'pendente'
        msg_retorno = ""

        if eh_quitacao_com_desconto:
            pag.valor_esperado = novo_valor_pago_acumulado
            pag.status = 'pago'
            novo_status = 'pago'
            msg_retorno = "Sucesso: Dívida quitada com desconto/ajuste."
        else:
            if novo_valor_pago_acumulado >= (divida_total - 0.05):
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
        
        if obs:
            pag.obs = (pag.obs or "") + " | " + obs
            
        self.dao_pagamento.atualizar(pag)

        # 2. Integração Financeira
        contrato = self.dao_contrato.buscar_por_id(pag.id_contrato_kitnet)
        kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
        inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
        
        identificacao = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "?"
        nome_inq = inquilino.nome if inquilino else "?"
        
        desc_lancamento = f"Aluguel {identificacao} ({nome_inq}) - Ref: {pag.mes_referencia}"
        if novo_status == 'parcial': desc_lancamento += " [PARCIAL]"
        if eh_quitacao_com_desconto: desc_lancamento += " [ACORDO]"

        self.fin_service.registrar_receita_manual(
            descricao=desc_lancamento, 
            valor=valor_recebido, 
            id_categoria=1,
            data=pag.data_pagamento, 
            banco=banco, 
            forma="Transferência/Pix",
            id_kitnet=kitnet.id_kitnet if kitnet else None,
            id_pagamento_aluguel=pag.id_aluguel
        )
        
        return msg_retorno

    def gerar_cobrancas_mensais(self) -> str:
        contratos = self.dao_contrato.listar_ativos()
        todos_pags = self.dao_pagamento.listar_todos()
        mes_atual = date.today().strftime("%Y-%m")
        count = 0

        for c in contratos:
            ja_existe = any(p.id_contrato_kitnet == c.id_contrato_kitnet and p.mes_referencia == mes_atual for p in todos_pags)
            
            if not ja_existe:
                valor_total = c.valor_fechado + (c.valor_esgoto_padrao or 0.0)
                self._criar_cobranca(c.id_contrato_kitnet, mes_atual, valor_total)
                count += 1
        
        return f"Processamento concluído. {count} novas cobranças geradas para {mes_atual}."

    # --- NOVO MÉTODO UNIFICADO ---
    def encerrar_contrato(self, id_locacao: int, data_saida: str, cobrar_multa: bool, valor_multa: float = 0.0) -> str:
        """
        Finaliza o contrato, libera a kitnet e opcionalmente lança a multa.
        """
        try:
            # 1. Busca contrato
            contrato = self.dao_contrato.buscar_por_id(id_locacao)
            if not contrato:
                return "Erro: Locação não encontrada."

            # 2. Atualiza Status do Contrato (Inativo)
            contrato.ativo = 0
            contrato.data_fim = data_saida
            self.dao_contrato.salvar(contrato) # Ou dao_contrato.atualizar(contrato) dependendo da sua impl

            # 3. Libera a Kitnet (Volta a ser 'LIVRE')
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            if kitnet:
                kitnet.status = 'LIVRE'
                self.dao_kitnet.atualizar(kitnet)

            # 4. Lógica da Multa (Se marcada)
            if cobrar_multa and valor_multa > 0:
                # Cria uma cobrança avulsa no sistema de aluguéis para ficar registrado
                self._criar_cobranca(
                    id_contrato=id_locacao, 
                    mes_ref="MULTA-RESC", 
                    valor_total_esperado=valor_multa
                )
                return "Contrato encerrado COM multa gerada (ver em Receber Aluguel)."
            
            return "Contrato encerrado e Kitnet liberada (SEM multa)."

        except Exception as e:
            return f"Erro ao encerrar: {e}"

    # --- MÉTODOS DE LEITURA PARA O FRONTEND ---

    def listar_ativas(self) -> List[Dict]:
        """Retorna lista de contratos ativos para a aba de Desocupação"""
        contratos = self.dao_contrato.listar_ativos()
        lista_formatada = []
        
        for c in contratos:
            k = self.dao_kitnet.buscar_por_id(c.id_kitnet)
            i = self.dao_inquilino.buscar_por_id(c.id_inquilino)
            
            lista_formatada.append({
                "id": c.id_contrato_kitnet,
                "numero": k.numero if k else "?",
                "identificador": k.identificador if k else "?",
                "inquilino_nome": i.nome if i else "Desconhecido",
                "data_inicio": c.data_inicio,
                "valor": c.valor_fechado,
                "dia_vencimento": c.data_vencimento
            })
        return lista_formatada

    def listar_alugueis_pendentes(self) -> List[Dict]:
        pendentes = self.dao_pagamento.listar_pendentes()
        resultado = []
        
        for p in pendentes:
            contrato = self.dao_contrato.buscar_por_id(p.id_contrato_kitnet)
            if not contrato: continue
            
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
            
            nome_kit = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "???"
            nome_inq = inquilino.nome if inquilino else "???"
            
            restante = p.valor_esperado - p.valor_pago
            
            resultado.append({
                "id_pagamento": p.id_aluguel,
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

    def _criar_cobranca(self, id_contrato, mes_ref, valor_total_esperado):
        novo_pag = PagamentoAluguel(
            id_contrato_kitnet=id_contrato, 
            mes_referencia=mes_ref,
            valor_esperado=valor_total_esperado,
            valor_pago=0.0, 
            status='pendente', 
            data_pagamento=None,
            obs=""
        )
        self.dao_pagamento.salvar(novo_pag)