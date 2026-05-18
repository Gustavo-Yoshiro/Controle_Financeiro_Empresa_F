import os
from typing import List, Dict, Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from Persistencia.Impl import ContratoKitnetImpl, PagamentoAluguelImpl, KitnetImpl, InquilinoImpl
from Persistencia.Entidades import ContratoKitnet, PagamentoAluguel
from Service import FinanceiroService

class LocacaoService:
    def __init__(self, financeiro_service: FinanceiroService = None):
        self.dao_contrato = ContratoKitnetImpl()
        self.dao_pagamento = PagamentoAluguelImpl()
        self.dao_kitnet = KitnetImpl()
        self.dao_inquilino = InquilinoImpl()
        self.fin_service = financeiro_service if financeiro_service else FinanceiroService()

    def _salvar_arquivo_disco(self, arquivo_obj, id_kitnet) -> Optional[str]:
        if not arquivo_obj:
            return None
            
        pasta_destino = "uploads_contratos"
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            
        data_hj = date.today().strftime("%Y%m%d")
        extensao = arquivo_obj.name.split('.')[-1] if '.' in arquivo_obj.name else 'arq'
        nome_limpo = f"contrato_k{id_kitnet}_{data_hj}.{extensao}"
        
        caminho_completo = os.path.join(pasta_destino, nome_limpo)
        
        try:
            with open(caminho_completo, "wb") as f:
                f.write(arquivo_obj.getbuffer())
            return caminho_completo
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return None

    def _salvar_comprovante(self, arquivo_obj, id_pagamento) -> Optional[str]:
        if not arquivo_obj:
            return None
            
        pasta_destino = "uploads_comprovantes"
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            
        data_hj = date.today().strftime("%Y%m%d_%H%M%S")
        extensao = arquivo_obj.name.split('.')[-1] if '.' in arquivo_obj.name else 'arq'
        nome_limpo = f"comprovante_pag{id_pagamento}_{data_hj}.{extensao}"
        
        caminho_completo = os.path.join(pasta_destino, nome_limpo)
        
        try:
            with open(caminho_completo, "wb") as f:
                f.write(arquivo_obj.getbuffer())
            return caminho_completo
        except Exception as e:
            print(f"Erro ao salvar comprovante: {e}")
            return None

    def alugar(self, id_kitnet: int, id_inquilino: int, valor_aluguel: float, dia_vencimento: int, 
               data_inicio: str, valor_esgoto: float = 0.0, data_fim: str = None, 
               mobiliado: int = 0, obs_mobiliado: str = "", arquivo_upload = None) -> str: 
        
        kitnet = self.dao_kitnet.buscar_por_id(id_kitnet)
        if kitnet.status != 'LIVRE': 
            return "Erro: Kitnet já ocupada."

        caminho_final_str = self._salvar_arquivo_disco(arquivo_upload, id_kitnet)

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
            pdf_caminho_contrato_kit=caminho_final_str
        )
        
        id_gerado = self.dao_contrato.salvar(novo_contrato)
        
        if id_gerado:
            kitnet.status = 'OCUPADA'
            self.dao_kitnet.atualizar(kitnet)

            mes_atual = str(data_inicio)[:7] 
            valor_total_mes = valor_aluguel + valor_esgoto
            self._criar_cobranca(id_gerado, mes_atual, valor_total_mes)
            
            return "Sucesso: Contrato fechado e Kitnet alugada!"
        return "Erro ao gerar contrato."

    def processar_pagamento_aluguel(self, id_pagamento: int, valor_recebido: float, banco: str, 
                                    eh_quitacao_com_desconto: bool = False, obs: str = "",
                                    arquivo_comprovante = None) -> str: 
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

        pag.valor_pago = novo_valor_pago_acumulado
        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        
        caminho_comprovante = self._salvar_comprovante(arquivo_comprovante, id_pagamento)
        
        texto_obs = obs
        if caminho_comprovante:
            texto_obs += f" | 📄 Comprovante: {caminho_comprovante}"

        if texto_obs: 
            pag.obs = (pag.obs or "") + " | " + texto_obs
            
        self.dao_pagamento.atualizar(pag)

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
        
        hoje = date.today()
        hoje_str = hoje.strftime("%Y-%m-%d")
        
        count_cobrancas = 0

        for c in contratos:

            try:
                dt_cursor = datetime.strptime(c.data_inicio, "%Y-%m-%d").date()
                dt_cursor = dt_cursor.replace(day=1)
                
                while dt_cursor <= hoje.replace(day=1):
                    mes_ref = dt_cursor.strftime("%Y-%m")
                    
                    ja_existe = any(p.id_contrato_kitnet == c.id_contrato_kitnet and p.mes_referencia == mes_ref for p in todos_pags)
                    
                    if not ja_existe:
                        valor_total = c.valor_fechado + (c.valor_esgoto_padrao or 0.0)
                        self._criar_cobranca(c.id_contrato_kitnet, mes_ref, valor_total)
                        count_cobrancas += 1
                    
                    dt_cursor += relativedelta(months=1)
                    
            except Exception as e:
                print(f"Erro ao processar contrato {c.id_contrato_kitnet}: {e}")
        
        msg = f"Processamento: {count_cobrancas} cobranças geradas (Contratos por prazo indeterminado mantidos ativos)."
            
        return msg

    def lancar_cobranca_variavel_em_lote(self, bloco_alvo: str, valor_por_inquilino: float, mes_ref: str, nome_taxa: str = "Taxa Variável") -> str:
        if valor_por_inquilino <= 0: return "Valor deve ser maior que zero."

        contratos_ativos = self.dao_contrato.listar_ativos()
        todos_pags = self.dao_pagamento.listar_todos()
        count_atualizados = 0
        
        for contrato in contratos_ativos:
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            if kitnet and kitnet.identificador == bloco_alvo:
                pag_alvo = None
                for p in todos_pags:
                    if p.id_contrato_kitnet == contrato.id_contrato_kitnet and p.mes_referencia == mes_ref:
                        pag_alvo = p
                        break
                
                if pag_alvo and pag_alvo.status != 'pago':
                    pag_alvo.valor_esperado += valor_por_inquilino
                    obs_add = f" [+ {nome_taxa}: R$ {valor_por_inquilino:.2f}]"
                    pag_alvo.obs = (pag_alvo.obs or "") + obs_add
                    self.dao_pagamento.atualizar(pag_alvo)
                    count_atualizados += 1
        
        if count_atualizados == 0:
            return f"Nenhum boleto aberto encontrado no bloco {bloco_alvo}."
        return f"Sucesso! {nome_taxa} lançada para {count_atualizados} inquilinos."

    # GESTÃO INDIVIDUAL DE DÍVIDAS E FATURAS 

    def listar_faturas_por_contrato(self, id_contrato: int) -> List[Dict]:
        """ Busca todas as faturas geradas para o contrato selecionado """
        todos = self.dao_pagamento.listar_todos()
        faturas_contrato = [p for p in todos if p.id_contrato_kitnet == id_contrato]
        
        faturas_contrato.sort(key=lambda x: x.mes_referencia, reverse=True)
        
        res = []
        for f in faturas_contrato:
            res.append({
                "id_pagamento": f.id_aluguel,
                "mes_referencia": f.mes_referencia,
                "valor_esperado": f.valor_esperado,
                "valor_pago": f.valor_pago or 0.0,
                "status": f.status,
                "obs": f.obs or ""
            })
        return res

    def deletar_fatura(self, id_pagamento: int) -> str:
        """ Cancela a fatura em vez de apagar do banco para o robô não recriar """
        try:
            pag = self.dao_pagamento.buscar_por_id(id_pagamento)
            if not pag: return "Erro: Fatura não encontrada."
            
            pag.status = 'pago'
            pag.valor_esperado = 0.0
            pag.obs = (pag.obs or "") + " [CANCELADA]"
            self.dao_pagamento.atualizar(pag)
            return "Fatura cancelada com sucesso (não será cobrada nem recriada)."
        except Exception as e:
            return f"Erro ao cancelar fatura: {e}"

    def atualizar_fatura(self, id_pagamento: int, novo_valor: float, nova_obs: str) -> str:
        """ Edita o valor esperado ou as anotações de uma fatura existente """
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Erro: Fatura não encontrada."
        
        pag.valor_esperado = novo_valor
        pag.obs = nova_obs
        self.dao_pagamento.atualizar(pag)
        return "Fatura atualizada com sucesso!"

    def lancar_divida_avulsa_individual(self, id_contrato: int, valor: float, mes_ref: str, descricao: str) -> str:
        if valor <= 0: return "Erro: O valor deve ser maior que zero."

        todos_pags = self.dao_pagamento.listar_todos()
        pag_alvo = None
        for p in todos_pags:
            if p.id_contrato_kitnet == id_contrato and p.mes_referencia == mes_ref:
                pag_alvo = p
                break

        if pag_alvo:
            if pag_alvo.status == 'pago':
                return "Erro: A fatura desse mês já está quitada. Lance em um mês pendente."
            
            pag_alvo.valor_esperado += valor
            obs_add = f" [+ {descricao}: R$ {valor:.2f}]"
            pag_alvo.obs = (pag_alvo.obs or "") + obs_add
            self.dao_pagamento.atualizar(pag_alvo)
            return f"Sucesso! Valor somado à fatura existente de {mes_ref}."
        else:
            self._criar_cobranca(id_contrato, mes_ref, valor)
            
            todos_pags_atualizados = self.dao_pagamento.listar_todos()
            for p in todos_pags_atualizados:
                if p.id_contrato_kitnet == id_contrato and p.mes_referencia == mes_ref:
                    p.obs = f"{descricao}"
                    self.dao_pagamento.atualizar(p)
                    break
            return f"Sucesso! Nova fatura criada para {mes_ref}."


    def encerrar_contrato(self, id_locacao: int, data_saida: str, cobrar_multa: bool, valor_multa: float = 0.0) -> str:
        try:
            contrato = self.dao_contrato.buscar_por_id(id_locacao)
            if not contrato: return "Erro: Locação não encontrada."

            contrato.ativo = 0
            contrato.data_fim = data_saida
            self.dao_contrato.salvar(contrato)

            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            if kitnet:
                kitnet.status = 'LIVRE'
                self.dao_kitnet.atualizar(kitnet)

            if cobrar_multa and valor_multa > 0:
                self._criar_cobranca(id_locacao, "MULTA-RESC", valor_multa)
                return "Contrato encerrado COM multa gerada."
            
            return "Contrato encerrado e Kitnet liberada (SEM multa)."
        except Exception as e:
            return f"Erro ao encerrar: {e}"

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
                "data_fim": c.data_fim,
                "valor": c.valor_fechado,
                "dia_vencimento": c.data_vencimento
            })
        return lista_formatada

    def listar_encerrados_renovaveis(self) -> List[Dict]:
        """ Busca contratos inativos onde a Kitnet está LIVRE e o Inquilino NÃO tem outro contrato """
        sql = "SELECT id_contrato_kitnet, id_kitnet, id_inquilino, data_fim, valor_fechado, valor_esgoto_padrao, data_vencimento, mobiliado FROM contrato_kitnet WHERE ativo = 0 ORDER BY data_fim DESC LIMIT 50"
        try:
            rows = self.dao_contrato.db.executar_query(sql)
        except Exception as e:
            print(f"Erro buscar inativos: {e}")
            return []
            
        lista = []
        ativos = self.dao_contrato.listar_ativos()
        inq_ativos = [a.id_inquilino for a in ativos]
        
        for r in rows:
            k = self.dao_kitnet.buscar_por_id(r[1])
            if k and str(k.status).strip().upper() == 'LIVRE':
                i = self.dao_inquilino.buscar_por_id(r[2])
                if i and i.id_inquilino not in inq_ativos:
                    lista.append({
                        "id_contrato": r[0],
                        "id_kitnet": r[1],
                        "id_inquilino": r[2],
                        "kitnet_label": f"{k.identificador}-{k.numero}",
                        "inquilino_nome": i.nome,
                        "data_fim_antigo": r[3] if r[3] else "Desconhecida",
                        "valor_fechado": r[4],
                        "valor_esgoto": r[5] if r[5] else 0.0,
                        "dia_vencimento": r[6],
                        "mobiliado": r[7] if r[7] else 0
                    })
        return lista

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