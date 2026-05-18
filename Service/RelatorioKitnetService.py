from datetime import date
from typing import List, Dict

from Persistencia.Impl import KitnetImpl, ContratoKitnetImpl, PagamentoAluguelImpl, InquilinoImpl

class RelatorioKitnetService:
    def __init__(self):
        self.dao_kitnet = KitnetImpl()
        self.dao_contrato = ContratoKitnetImpl()
        self.dao_pagamento = PagamentoAluguelImpl()
        self.dao_inquilino = InquilinoImpl()

    def gerar_painel_geral(self, mes_ref: str = None) -> List[dict]:
        """
        Gera dados da tabela. Se mes_ref for None, usa o mês atual.
        Formato mes_ref: 'YYYY-MM' (Ex: '2023-12')
        """
        todas_kits = self.dao_kitnet.listar_todas()
        contratos_ativos = self.dao_contrato.listar_ativos()
        
        todos_pagamentos = self.dao_pagamento.listar_todos()
        todos_inquilinos = self.dao_inquilino.listar_todos()
        
        if not mes_ref:
            mes_ref = date.today().strftime("%Y-%m")

        tabela = []
        for k in todas_kits:
            nome_visual = f"{k.identificador}-{k.numero}"
            linha = {
                "ID": k.id_kitnet, 
                "Identificação": nome_visual, 
                "Status Imóvel": k.status, 
                "Inquilino": "---", 
                "Vencimento": "---", 
                "Situação Mês": "LIVRE",
                "Valor Base": f"R$ {k.preco_padrao:.2f}",
                "Alertas": ""
            }
            
            if k.status == 'OCUPADA':
                contrato = next((c for c in contratos_ativos if c.id_kitnet == k.id_kitnet), None)
                if contrato:
                    inq = next((i for i in todos_inquilinos if i.id_inquilino == contrato.id_inquilino), None)
                    linha["Inquilino"] = inq.nome if inq else "?"
                    linha["Vencimento"] = f"Dia {contrato.data_vencimento}"
                    
                    pags_do_contrato = [p for p in todos_pagamentos if p.id_contrato_kitnet == contrato.id_contrato_kitnet]
                    
                    divida_acumulada = 0.0
                    qtd_atrasados = 0
                    for p in pags_do_contrato:
                        if p.mes_referencia < mes_ref: 
                            if p.status in ['pendente', 'atrasado', 'parcial']:
                                falta = p.valor_esperado - p.valor_pago
                                if falta > 0.05:
                                    divida_acumulada += falta
                                    qtd_atrasados += 1
                    
                    if qtd_atrasados > 0:
                        linha["Alertas"] = f"⚠️ {qtd_atrasados} boletos (R$ {divida_acumulada:.2f})"

                    pag_mes = next((p for p in pags_do_contrato if p.mes_referencia == mes_ref), None) # <--- MUDOU AQUI
                    
                    if not pag_mes:
                        linha["Situação Mês"] = "⚪ Aguardando Cobrança"
                    else:
                        status_bd = pag_mes.status
                        if status_bd == 'pago':
                            linha["Situação Mês"] = "✅ PAGO"
                        elif status_bd == 'parcial':
                            restante = pag_mes.valor_esperado - pag_mes.valor_pago
                            linha["Situação Mês"] = f"🟡 PARCIAL (Falta R$ {restante:.2f})"
                        else: 
                            hoje_str = date.today().strftime("%Y-%m-%d")
                            vencimento_str = f"{mes_ref}-{contrato.data_vencimento:02d}"
                            
                            if hoje_str > vencimento_str:
                                linha["Situação Mês"] = f"🔴 ATRASADO ({contrato.data_vencimento})"
                            else:
                                linha["Situação Mês"] = "⏳ A VENCER"

            tabela.append(linha)
        
        tabela.sort(key=lambda x: x['Identificação'])
        return tabela

    def listar_pendencias_formatadas(self) -> Dict[str, int]:
        pagamentos = self.dao_pagamento.listar_pendentes() 
        opcoes = {}
        
        for pag in pagamentos:
            contrato = self.dao_contrato.buscar_por_id(pag.id_contrato_kitnet)
            if contrato:
                k = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
                i = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
                
                ident = k.identificador if k else "K"
                num = k.numero if k else "?"
                nome_i = i.nome if i else "?"
                
                valor_mostrar = pag.valor_esperado - pag.valor_pago
                
                texto = f"{ident}-{num} | {nome_i} | Ref: {pag.mes_referencia} | Falta R$ {valor_mostrar:.2f}"
                opcoes[texto] = pag.id_aluguel 
        return opcoes