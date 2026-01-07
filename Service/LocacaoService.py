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

    def alugar(self, id_kitnet: int, id_inquilino: int, valor: float, dia_vencimento: int, 
               data_inicio: str, data_fim: str = None, mobiliado: int = 0, obs: str = "") -> str:
        
        # 1. Verifica disponibilidade
        kitnet = self.dao_kitnet.buscar_por_id(id_kitnet)
        if kitnet.status != 'LIVRE': 
            return "Erro: Kitnet já ocupada."

        # 2. Cria o contrato
        novo_contrato = ContratoKitnet(
            id_kitnet=id_kitnet, 
            id_inquilino=id_inquilino, 
            valor_fechado=valor,
            data_vencimento=dia_vencimento, 
            data_inicio=data_inicio, 
            data_fim=data_fim,
            ativo=1,
            mobiliado=mobiliado,
            obs_mobiliado=obs,
            pdf_caminho_contrato_kit=None # Futuramente pode passar o caminho do arquivo
        )
        
        id_gerado = self.dao_contrato.salvar(novo_contrato)
        
        if id_gerado:
            # 3. Atualiza Status da Kitnet para OCUPADA
            kitnet.status = 'OCUPADA'
            self.dao_kitnet.atualizar(kitnet)

            # 4. Gera a primeira cobrança (Boleto interno do aluguel)
            mes_atual = str(data_inicio)[:7] # Ex: '2025-01'
            self._criar_cobranca(id_gerado, mes_atual, valor)
            
            return "Sucesso: Contrato fechado e Kitnet alugada!"
        return "Erro ao gerar contrato."

    def processar_pagamento_aluguel(self, id_pagamento: int, valor_recebido: float, banco: str) -> str:
        pag = self.dao_pagamento.buscar_por_id(id_pagamento)
        if not pag: return "Pagamento não encontrado."
        if pag.status == 'pago': return "Erro: Já foi pago."

        # Recupera dados para descrever bem no extrato
        contrato = self.dao_contrato.buscar_por_id(pag.id_contrato_kitnet)
        kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
        inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
        
        identificacao = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "?"
        nome_inq = inquilino.nome if inquilino else "?"

        # 1. Atualiza no módulo de Locação
        pag.valor_pago = valor_recebido
        pag.status = 'pago'
        pag.data_pagamento = date.today().strftime("%Y-%m-%d")
        self.dao_pagamento.atualizar(pag)

        # 2. Integração Financeira (Lança Receita)
        desc_lancamento = f"Aluguel {identificacao} ({nome_inq}) - Ref: {pag.mes_referencia}"
        
        self.fin_service.registrar_receita_manual(
            descricao=desc_lancamento, 
            valor=valor_recebido, 
            id_categoria=1, 
            data=pag.data_pagamento, 
            banco=banco, 
            forma="Transferência/Pix"
        )
        return "Recebimento processado e lançado no caixa."

    def gerar_cobrancas_mensais(self) -> str:
        """
        Método Rotineiro: Verifica contratos ativos e gera a cobrança 
        do mês atual para quem ainda não tem.
        """
        contratos = self.dao_contrato.listar_ativos()
        todos_pags = self.dao_pagamento.listar_todos()
        mes_atual = date.today().strftime("%Y-%m")
        count = 0

        for c in contratos:
            # Verifica se já existe pagamento gerado para este contrato neste mês
            ja_existe = any(p.id_contrato_kitnet == c.id_contrato_kitnet and p.mes_referencia == mes_atual for p in todos_pags)
            
            if not ja_existe:
                self._criar_cobranca(c.id_contrato_kitnet, mes_atual, c.valor_fechado)
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

    def _criar_cobranca(self, id_contrato, mes_ref, valor_base):
        # Cria o registro "Pendente" na tabela de pagamentos
        # Note que o 'valor_pago' começa zerado, pois é pendente
        # Mas poderíamos ter um campo 'valor_esperado' no banco futuramente.
        novo_pag = PagamentoAluguel(
            id_contrato_kitnet=id_contrato, 
            mes_referencia=mes_ref,
            valor_pago=0.0, # Ainda não pagou
            status='pendente', 
            data_pagamento=None
        )
        # Opcional: injetar valor esperado dinamicamente na UI usando valor_base
        self.dao_pagamento.salvar(novo_pag)

    def listar_alugueis_pendentes(self) -> List[Dict]:
        """Retorna lista formatada para a tela de Recebimentos"""
        pendentes = self.dao_pagamento.listar_pendentes()
        resultado = []
        
        for p in pendentes:
            # Busca dados extras para exibir bonito na tela
            contrato = self.dao_contrato.buscar_por_id(p.id_contrato_kitnet)
            if not contrato: continue
            
            kitnet = self.dao_kitnet.buscar_por_id(contrato.id_kitnet)
            inquilino = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
            
            nome_kit = f"{kitnet.identificador}-{kitnet.numero}" if kitnet else "???"
            nome_inq = inquilino.nome if inquilino else "???"
            
            resultado.append({
                "id_pagamento": p.id_aluguel,
                "descricao": f"{nome_kit} - {nome_inq}",
                "mes": p.mes_referencia,
                "valor_esperado": contrato.valor_fechado, 
                "vencimento_dia": contrato.data_vencimento
            })
        return resultado