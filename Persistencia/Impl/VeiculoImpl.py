from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Veiculo import Veiculo

class VeiculoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, veiculo: Veiculo) -> int:
        sql = "INSERT INTO veiculo (modelo, placa, ano, km_atual, finalidade, status) VALUES (?, ?, ?, ?, ?, ?)"
        parametros = (veiculo.modelo, veiculo.placa, veiculo.ano, veiculo.km_atual, veiculo.finalidade, veiculo.status)
        id_gerado = self.__bd.executar(sql, parametros)
        veiculo.id_veiculo = id_gerado
        return id_gerado

    def atualizar(self, veiculo: Veiculo) -> None:
        sql = "UPDATE veiculo SET modelo=?, placa=?, ano=?, km_atual=?, finalidade=?, status=? WHERE id_veiculo=?"
        parametros = (veiculo.modelo, veiculo.placa, veiculo.ano, veiculo.km_atual, veiculo.finalidade, veiculo.status, veiculo.id_veiculo)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_veiculo: int) -> None:
        sql = "DELETE FROM veiculo WHERE id_veiculo = ?"
        self.__bd.executar(sql, (id_veiculo,))

    def buscar_por_id(self, id_veiculo: int) -> Optional[Veiculo]:
        sql = "SELECT id_veiculo, modelo, placa, ano, km_atual, finalidade, status FROM veiculo WHERE id_veiculo = ?"
        row = self.__bd.executar_query(sql, (id_veiculo,), fetchone=True)
        if row:
            return Veiculo(id_veiculo=row[0], modelo=row[1], placa=row[2], ano=row[3], km_atual=row[4], finalidade=row[5], status=row[6])
        return None

    def listar_todos(self) -> List[Veiculo]:
        sql = "SELECT id_veiculo, modelo, placa, ano, km_atual, finalidade, status FROM veiculo"
        rows = self.__bd.executar_query(sql)
        return [Veiculo(id_veiculo=r[0], modelo=r[1], placa=r[2], ano=r[3], km_atual=r[4], finalidade=r[5], status=r[6]) for r in rows]
