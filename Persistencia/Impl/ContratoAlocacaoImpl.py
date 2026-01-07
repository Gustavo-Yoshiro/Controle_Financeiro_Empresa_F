from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import ContratoAlocacao

class ContratoAlocacaoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, contrato: ContratoAlocacao) -> int:
        # PADRÃO INTELIGENTE: Se tem ID, atualiza. Se não, cria.
        if contrato.id_contrato_alocacao:
            self.atualizar(contrato)
            return contrato.id_contrato_alocacao
        else:
            sql = """INSERT INTO contrato_alocacao (id_empresa, id_veiculo, valor_mensal, dia_vencimento, ativo) 
                     VALUES (?, ?, ?, ?, ?)"""
            parametros = (contrato.id_empresa, contrato.id_veiculo, contrato.valor_mensal, contrato.dia_vencimento, contrato.ativo)
            id_gerado = self.__bd.executar(sql, parametros)
            contrato.id_contrato_alocacao = id_gerado
            return id_gerado

    def atualizar(self, contrato: ContratoAlocacao) -> None:
        sql = """UPDATE contrato_alocacao SET id_empresa=?, id_veiculo=?, valor_mensal=?, dia_vencimento=?, ativo=? 
                 WHERE id_contrato_alocacao=?"""
        parametros = (contrato.id_empresa, contrato.id_veiculo, contrato.valor_mensal, contrato.dia_vencimento, contrato.ativo, contrato.id_contrato_alocacao)
        self.__bd.executar(sql, parametros)

    def deletar(self, id_contrato: int) -> None:
        self.__bd.executar("DELETE FROM contrato_alocacao WHERE id_contrato_alocacao=?", (id_contrato,))

    def listar_ativos(self) -> List[ContratoAlocacao]:
        sql = "SELECT id_contrato_alocacao, id_empresa, id_veiculo, valor_mensal, dia_vencimento, ativo FROM contrato_alocacao WHERE ativo = 1"
        rows = self.__bd.executar_query(sql)
        return [ContratoAlocacao(id_contrato_alocacao=r[0], id_empresa=r[1], id_veiculo=r[2], valor_mensal=r[3], dia_vencimento=r[4], ativo=r[5]) for r in rows]
    
    def buscar_por_id(self, id_contrato: int) -> Optional[ContratoAlocacao]:
        sql = "SELECT id_contrato_alocacao, id_empresa, id_veiculo, valor_mensal, dia_vencimento, ativo FROM contrato_alocacao WHERE id_contrato_alocacao = ?"
        row = self.__bd.executar_query(sql, (id_contrato,), fetchone=True)
        
        if row:
            return ContratoAlocacao(
                id_contrato_alocacao=row[0], 
                id_empresa=row[1], 
                id_veiculo=row[2], 
                valor_mensal=row[3], 
                dia_vencimento=row[4], 
                ativo=row[5]
            )
        return None