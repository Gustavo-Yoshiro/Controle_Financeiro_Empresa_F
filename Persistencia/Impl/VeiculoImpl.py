from typing import List, Dict, Optional
from Persistencia.Banco import BancoDeDados

class VeiculoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, modelo: str, placa: str, ano: int, finalidade: str) -> int:
        """
        Cadastra um novo veículo.
        Status padrão é 'ativo'.
        """
        sql = """
        INSERT INTO veiculo (modelo, placa, ano, finalidade, status)
        VALUES (?, ?, ?, ?, 'ativo')
        """
        id_gerado = self.__bd.executar(sql, (modelo, placa, ano, finalidade))
        return id_gerado

    def listar_todos(self) -> List[Dict]:
        """
        Retorna todos os veículos para exibir na lista ou no selectbox.
        """
        sql = "SELECT id_veiculo, modelo, placa, ano, finalidade, status FROM veiculo"
        rows = self.__bd.executar_query(sql)
        
        lista = []
        for r in rows:
            lista.append({
                "id": r[0],
                "modelo": r[1],
                "placa": r[2],
                "ano": r[3],
                "finalidade": r[4],
                "status": r[5]
            })
        return lista

    def buscar_por_id(self, id_veiculo: int) -> Optional[Dict]:
        """Busca um único veículo."""
        sql = "SELECT id_veiculo, modelo, placa, ano, finalidade, status FROM veiculo WHERE id_veiculo = ?"
        row = self.__bd.executar_query(sql, (id_veiculo,), fetchone=True)
        
        if row:
            return {
                "id": row[0],
                "modelo": row[1],
                "placa": row[2],
                "ano": row[3],
                "finalidade": row[4],
                "status": row[5]
            }
        return None

    def atualizar_status(self, id_veiculo: int, novo_status: str):
        """
        Muda o status (Ex: de 'ativo' para 'oficina').
        """
        sql = "UPDATE veiculo SET status = ? WHERE id_veiculo = ?"
        self.__bd.executar(sql, (novo_status, id_veiculo))