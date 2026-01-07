from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import Veiculo

class VeiculoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, veiculo: Veiculo) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if veiculo.id_veiculo:
            self.atualizar(veiculo)
            return veiculo.id_veiculo
        else:
            sql = "INSERT INTO veiculo (modelo, placa, ano, finalidade, status) VALUES (?, ?, ?, ?, ?)"
            id_gerado = self.__bd.executar(sql, (veiculo.modelo, veiculo.placa, veiculo.ano, veiculo.finalidade, veiculo.status))
            veiculo.id_veiculo = id_gerado
            return id_gerado

    def atualizar(self, veiculo: Veiculo):
        sql = "UPDATE veiculo SET modelo=?, placa=?, ano=?, finalidade=?, status=? WHERE id_veiculo=?"
        self.__bd.executar(sql, (veiculo.modelo, veiculo.placa, veiculo.ano, veiculo.finalidade, veiculo.status, veiculo.id_veiculo))

    def deletar(self, id_veiculo: int):
        self.__bd.executar("DELETE FROM veiculo WHERE id_veiculo=?", (id_veiculo,))

    def buscar_por_id(self, id_veiculo: int) -> Optional[Veiculo]:
        sql = "SELECT id_veiculo, modelo, placa, ano, finalidade, status FROM veiculo WHERE id_veiculo=?"
        row = self.__bd.executar_query(sql, (id_veiculo,), fetchone=True)
        if row:
            return Veiculo(id_veiculo=row[0], modelo=row[1], placa=row[2], ano=row[3], finalidade=row[4], status=row[5])
        return None

    def listar_todos(self) -> List[Veiculo]:
        sql = "SELECT id_veiculo, modelo, placa, ano, finalidade, status FROM veiculo"
        rows = self.__bd.executar_query(sql)
        return [Veiculo(id_veiculo=r[0], modelo=r[1], placa=r[2], ano=r[3], finalidade=r[4], status=r[5]) for r in rows]