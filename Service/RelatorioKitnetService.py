from datetime import date
from typing import List, Dict

from Persistencia.Impl import KitnetImpl, ContratoKitnetImpl, PagamentoAluguelImpl, InquilinoImpl

class RelatorioKitnetService:
    def __init__(self):
        self.dao_kitnet = KitnetImpl()
        self.dao_contrato = ContratoKitnetImpl()
        self.dao_pagamento = PagamentoAluguelImpl()
        self.dao_inquilino = InquilinoImpl()

    def montar_dashboard_kitnets(self) -> List[dict]:
        """
        Gera os dados para a tabela principal da tela de Kitnets.
        Formata status, emojis e situações de pagamento para exibição direta no Grid.
        """
        todas_kits = self.dao_kitnet.listar_todas()
        contratos_ativos = self.dao_contrato.listar_ativos()
        
        # Otimização: Carrega pagamentos do mês na memória
        # Isso evita fazer 1 query por kitnet dentro do loop (Problema N+1)
        todos_pagamentos = self.dao_pagamento.listar_todos()
        mes_atual = date.today().strftime("%Y-%m")
        pagamentos_mes = [p for p in todos_pagamentos if p.mes_referencia == mes_atual]

        tabela = []
        for k in todas_kits:
            # Dados base da Kitnet
            nome_visual = f"{k.identificador}-{k.numero}"
            linha = {
                "id": k.id_kitnet, 
                "numero": nome_visual, 
                "quartos": k.quartos,
                "valor_base": k.preco_padrao,
                "status": k.status, 
                "inquilino": "-", 
                "vencimento": "-", 
                "situacao_pagamento": "LIVRE"
            }
            
            # Se estiver ocupada, busca detalhes do contrato e pagamento
            if k.status == 'OCUPADA':
                # Busca o contrato ativo desta kitnet
                contrato = next((c for c in contratos_ativos if c.id_kitnet == k.id_kitnet), None)
                
                if contrato:
                    # Busca nome do inquilino
                    inq = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
                    linha["inquilino"] = inq.nome if inq else "Erro de Dados"
                    linha["vencimento"] = f"Dia {contrato.data_vencimento}"
                    linha["valor_fechado"] = contrato.valor_fechado

                    # Busca se já pagou este mês
                    pg = next((p for p in pagamentos_mes if p.id_contrato_kitnet == contrato.id_contrato_kitnet), None)
                    
                    if not pg:
                        linha["situacao_pagamento"] = "⚠️ S/ BOLETO"
                    elif pg.status == 'pago':
                        linha["situacao_pagamento"] = "✅ PAGO"
                    else:
                        # Verifica se está atrasado
                        hoje = date.today().day
                        if hoje > contrato.data_vencimento:
                            linha["situacao_pagamento"] = "🔴 ATRASADO"
                        else:
                            linha["situacao_pagamento"] = "⏳ PENDENTE"

            tabela.append(linha)
            
        # Ordena visualmente: Identificador (K/C) depois Número
        tabela.sort(key=lambda x: x['numero'])
        return tabela

    def listar_pendencias_formatadas(self) -> Dict[str, int]:
        """
        Retorna dicionário { 'K-101 | João | R$ 800': id_pagamento }
        Usado para preencher o SelectBox na tela de Recebimento de Aluguel.
        """
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
                
                # Formata texto amigável para o usuário escolher
                texto = f"{ident}-{num} | {nome_i} | Ref: {pag.mes_referencia} | R$ {contrato.valor_fechado:.2f}"
                
                opcoes[texto] = pag.id_aluguel 
        return opcoes