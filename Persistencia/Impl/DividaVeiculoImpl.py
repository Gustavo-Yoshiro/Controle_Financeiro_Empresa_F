from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import DividaVeiculo

class DividaVeiculoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, divida: DividaVeiculo) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if divida.id_divida:
            self.atualizar(divida)
            return divida.id_divida
        else:
            sql = "INSERT INTO divida_veiculo (id_veiculo, descricao, valor, data_vencimento, status) VALUES (?, ?, ?, ?, ?)"
            parametros = (divida.id_veiculo, divida.descricao, divida.valor, divida.data_vencimento, divida.status)
            id_gerado = self.__bd.executar(sql, parametros)
            divida.id_divida = id_gerado
            return id_gerado

    def atualizar(self, divida: DividaVeiculo) -> None:
        sql = "UPDATE divida_veiculo SET id_veiculo=?, descricao=?, valor=?, data_vencimento=?, status=? WHERE id_divida=?"
        parametros = (divida.id_veiculo, divida.descricao, divida.valor, divida.data_vencimento, divida.status, divida.id_divida)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_divida: int) -> None:
        sql = "DELETE FROM divida_veiculo WHERE id_divida = ?"
        self.__bd.executar(sql, (id_divida,))

    def listar_por_veiculo(self, id_veiculo: int) -> List[DividaVeiculo]:
        sql = "SELECT id_divida, id_veiculo, descricao, valor, data_vencimento, status FROM divida_veiculo WHERE id_veiculo = ?"
        rows = self.__bd.executar_query(sql, (id_veiculo,))
        return [DividaVeiculo(id_divida=r[0], id_veiculo=r[1], descricao=r[2], valor=r[3], data_vencimento=r[4], status=r[5]) for r in rows]

    # --- NOVO MÉTODO ADICIONADO AQUI ---
    def listar_todas(self) -> List[DividaVeiculo]:
        """Lista todas as dívidas de todos os veículos (Usado no Dashboard Financeiro)"""
        sql = "SELECT id_divida, id_veiculo, descricao, valor, data_vencimento, status FROM divida_veiculo ORDER BY data_vencimento ASC"
        rows = self.__bd.executar_query(sql)
        return [
            DividaVeiculo(
                id_divida=r[0], 
                id_veiculo=r[1], 
                descricao=r[2], 
                valor=r[3], 
                data_vencimento=r[4], 
                status=r[5]
            ) for r in rows
        ]

    def buscar_por_id(self, id_divida: int) -> Optional[DividaVeiculo]:
        sql = "SELECT id_divida, id_veiculo, descricao, valor, data_vencimento, status FROM divida_veiculo WHERE id_divida = ?"
        row = self.__bd.executar_query(sql, (id_divida,), fetchone=True)
        
        if row:
            return DividaVeiculo(
                id_divida=row[0], 
                id_veiculo=row[1], 
                descricao=row[2], 
                valor=row[3], 
                data_vencimento=row[4], 
                status=row[5]
            )
        return None