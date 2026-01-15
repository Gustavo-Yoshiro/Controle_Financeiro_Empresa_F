import os
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

    # --- MÉTODO AUXILIAR PARA SALVAR ARQUIVO (PRIVADO) ---
    def _salvar_arquivo_disco(self, arquivo_obj, id_kitnet) -> Optional[str]:
        """Recebe o objeto do Streamlit e salva na pasta do projeto"""
        if not arquivo_obj:
            return None
            
        pasta_destino = "uploads_contratos"
        # Cria a pasta se não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            
        # Gera um nome seguro: contrato_kitID_data_NomeOriginal
        data_hj = date.today().strftime("%Y%m%d")
        # Pega a extensão original do arquivo
        extensao = arquivo_obj.name.split('.')[-1] if '.' in arquivo_obj.name else 'arq'
        nome_limpo = f"contrato_k{id_kitnet}_{data_hj}.{extensao}"
        
        caminho_completo = os.path.join(pasta_destino, nome_limpo)
        
        # Salva os bytes no disco
        try:
            with open(caminho_completo, "wb") as f:
                f.write(arquivo_obj.getbuffer())
            return caminho_completo
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return None

    def alugar(self, id_kitnet: int, id_inquilino: int, valor_aluguel: float, dia_vencimento: int, 
               data_inicio: str, valor_esgoto: float = 0.0, data_fim: str = None, 
               mobiliado: int = 0, obs_mobiliado: str = "", arquivo_upload = None) -> str: 
        
        # 1. Verifica disponibilidade
        kitnet = self.dao_kitnet.buscar_por_id(id_kitnet)
        if kitnet.status != 'LIVRE': 
            return "Erro: Kitnet já ocupada."

        # 2. Lógica de Salvar Arquivo (Resolvemos isso ANTES de ir pro banco)
        caminho_final_str = self._salvar_arquivo_disco(arquivo_upload, id_kitnet)

        # 3. Cria o contrato
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
            obs_mobiliado=obs_mobiliado,
            pdf_caminho_contrato_kit=caminho_final_str # <--- Grava o caminho no banco
        )
        
        id_gerado = self.dao_contrato.salvar(novo_contrato)
        
        if id_gerado:
            # 4. Atualiza Status da Kitnet para OCUPADA
            kitnet.status = 'OCUPADA'
            self.dao_kitnet.atualizar(kitnet)

            # 5. Gera a primeira cobrança (Boleto interno)
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

    # --- NOVO MÉTODO PARA TAXAS VARIÁVEIS EM LOTE ---
    def lancar_cobranca_variavel_em_lote(self, bloco_alvo: str, valor_por_inquilino: float, mes_ref: str, nome_taxa: str = "Taxa Variável") -> str:
        """
        Adiciona um valor extra (água/esgoto) a todos os inquilinos ativos de um determinado Bloco
        no mês de referência.
        """
        if valor_por_inquilino <= 0:
            return "Valor deve ser maior que zero."

        # 1. Listar contratos ativos
        contratos_ativos = self.dao_contrato.listar_ativos()
        count_atualizados = 0
        
        # 2. Listar pagamentos já gerados para otimizar busca (ou buscar um por um)
        todos_pags = self.dao_pagamento.listar_todos() # Ideal seria filtrar por mês no DAO, mas manterei simples
        
        for contrato in contratos_ativos:
            # 2.1 Verifica se a Kitnet pertence ao bloco
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            if kitnet and kitnet.identificador == bloco_alvo:
                
                # 2.2 Encontra o boleto do mês
                pag_alvo = None
                for p in todos_pags:
                    if p.id_contrato_kitnet == contrato.id_contrato_kitnet and p.mes_referencia == mes_ref:
                        pag_alvo = p
                        break
                
                # 2.3 Atualiza o boleto se encontrado e não pago
                if pag_alvo and pag_alvo.status != 'pago':
                    pag_alvo.valor_esperado += valor_por_inquilino
                    
                    obs_add = f" [+ {nome_taxa}: R$ {valor_por_inquilino:.2f}]"
                    if pag_alvo.obs:
                        pag_alvo.obs += obs_add
                    else:
                        pag_alvo.obs = obs_add.strip()
                    
                    self.dao_pagamento.atualizar(pag_alvo)
                    count_atualizados += 1
        
        if count_atualizados == 0:
            return f"Nenhum inquilino encontrado no bloco {bloco_alvo} com boleto aberto para {mes_ref}."
            
        return f"Sucesso! Taxa de {nome_taxa} (R$ {valor_por_inquilino:.2f}) lançada para {count_atualizados} inquilinos do Bloco {bloco_alvo}."

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
            self.dao_contrato.salvar(contrato)

            # 3. Libera a Kitnet (Volta a ser 'LIVRE')
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            if kitnet:
                kitnet.status = 'LIVRE'
                self.dao_kitnet.atualizar(kitnet)

            # 4. Lógica da Multa (Se marcada)
            if cobrar_multa and valor_multa > 0:
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