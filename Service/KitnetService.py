from typing import List, Optional
from datetime import date

# Importando as implementações e entidades
from Persistencia.Impl import KitnetImpl, InquilinoImpl, ContratoKitnetImpl, PagamentoAluguelImpl
from Persistencia.Entidades import Kitnet, ContratoKitnet, PagamentoAluguel

# CORREÇÃO 1: Importar a classe de dentro do arquivo
from Service.FinanceiroService import FinanceiroService

class KitnetService:
    def __init__(self):
        self.dao_kitnet = KitnetImpl()
        self.dao_contrato = ContratoKitnetImpl()
        self.dao_pagamento = PagamentoAluguelImpl()
        
        # CORREÇÃO 2: Instanciar Inquilino aqui (uma vez só)
        self.dao_inquilino = InquilinoImpl()
        
        # CORREÇÃO 3: Nome mais limpo e importação correta
        self.fin_service = FinanceiroService()

    def cadastrar_kitnet(self, numero: int, valor: float, quartos: int = 1, status: str = 'LIVRE') -> str:
        nova_kit = Kitnet(
            numero=numero,
            quartos=quartos,
            preco_padrao=valor,
            status=status
        )
        self.dao_kitnet.salvar(nova_kit)
        return f"Sucesso: Kitnet {numero} cadastrada!"

    def alugar_kitnet(self, id_kitnet: int, id_inquilino: int, valor: float, dia_vencimento: int, data_inicio: str) -> str:
        # 1. Validações
        kitnet = self.dao_kitnet.buscar_por_id(id_kitnet)
        if not kitnet:
            return "Erro: Kitnet não encontrada."
        
        if kitnet.status != 'LIVRE':
            return f"Erro: A Kitnet {kitnet.numero} já está ocupada."

        # 2. Cria o Contrato
        novo_contrato = ContratoKitnet(
            id_kitnet=id_kitnet,
            id_inquilino=id_inquilino,
            valor_fechado=valor,
            data_vencimento=dia_vencimento,
            data_inicio=data_inicio,
            ativo=1
        )
        self.dao_contrato.salvar(novo_contrato)

        # 3. Muda status da Kitnet
        kitnet.status = 'OCUPADA'
        self.dao_kitnet.atualizar(kitnet)

        return "Sucesso: Contrato criado e Kitnet marcada como ocupada."

    def encerrar_contrato(self, id_contrato: int, data_fim: str) -> str:
        contratos = self.dao_contrato.listar_ativos()
        # Busca segura comparando Inteiros
        contrato_alvo = next((c for c in contratos if c.id_contrato_kitnet == int(id_contrato)), None)

        if not contrato_alvo:
            return "Erro: Contrato não encontrado."

        # 1. Desativa contrato
        contrato_alvo.ativo = 0
        contrato_alvo.data_fim = data_fim
        self.dao_contrato.atualizar(contrato_alvo)

        # 2. Libera a Kitnet
        kitnet = self.dao_kitnet.buscar_por_id(contrato_alvo.id_kitnet)
        if kitnet:
            kitnet.status = 'LIVRE'
            self.dao_kitnet.atualizar(kitnet)

        return "Sucesso: Contrato encerrado."

    def listar_kitnets_tabela(self) -> List[dict]:
        todas_kits = self.dao_kitnet.listar_todas()
        contratos_ativos = self.dao_contrato.listar_ativos()
        
        # O dao_inquilino já foi instanciado no __init__, não precisa criar de novo aqui

        tabela = []
        for k in todas_kits:
            linha = {
                "id": k.id_kitnet, # Útil para ações de botão
                "numero": f"K-{k.numero}",
                "valor": k.preco_padrao,
                "status": k.status,
                "inquilino": "-",
                "vencimento": "-"
            }

            if k.status == 'OCUPADA':
                contrato = next((c for c in contratos_ativos if c.id_kitnet == k.id_kitnet), None)
                if contrato:
                    # Usa o self.dao_inquilino carregado no init
                    inq = self.dao_inquilino.buscar_por_id(contrato.id_inquilino)
                    linha["inquilino"] = inq.nome if inq else "Erro cadastro"
                    linha["vencimento"] = f"Dia {contrato.data_vencimento}"
            
            tabela.append(linha)
        
        return tabela
    
    def realizar_recebimento_aluguel(self, id_pagamento: int, valor: float, banco: str) -> str:
        # Usa o nome corrigido 'fin_service'
        return self.fin_service.receber_aluguel(id_pagamento, valor, banco_destino=banco)