from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.Boleto import Boleto

class BoletoImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, boleto: Boleto) -> int:
        if boleto.id_boleto:
            # UPDATE
            sql = """UPDATE boleto SET descricao=?, valor=?, data_vencimento=?, codigo_barras=?, 
                     id_categoria=?, status=?, obs=?, banco_pagamento=? WHERE id_boleto=?"""
            params = (boleto.descricao, boleto.valor, boleto.data_vencimento, boleto.codigo_barras, 
                      boleto.id_categoria, boleto.status, boleto.obs, boleto.banco_pagamento, boleto.id_boleto)
            self.__bd.executar(sql, params)
        else:
            # INSERT
            sql = """INSERT INTO boleto (descricao, valor, data_vencimento, codigo_barras, id_categoria, status, obs, banco_pagamento)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (boleto.descricao, boleto.valor, boleto.data_vencimento, boleto.codigo_barras, 
                      boleto.id_categoria, boleto.status, boleto.obs, boleto.banco_pagamento)
            boleto.id_boleto = self.__bd.executar(sql, params)
            
        return boleto.id_boleto

    def registrar_pagamento(self, id_boleto: int, banco: str):
        """Marca como pago e salva o banco usado"""
        sql = "UPDATE boleto SET status='pago', banco_pagamento=? WHERE id_boleto=?"
        self.__bd.executar(sql, (banco, id_boleto))

    def atualizar_status(self, id_boleto: int, status: str):
        sql = "UPDATE boleto SET status=? WHERE id_boleto=?"
        self.__bd.executar(sql, (status, id_boleto))

    def excluir(self, id_boleto: int):
        sql = "DELETE FROM boleto WHERE id_boleto=?"
        self.__bd.executar(sql, (id_boleto,))

    def buscar_por_id(self, id_boleto: int) -> Optional[Boleto]:
        sql = """SELECT id_boleto, descricao, valor, data_vencimento, id_categoria, 
                 codigo_barras, status, obs, banco_pagamento FROM boleto WHERE id_boleto = ?"""
        row = self.__bd.executar_query(sql, (id_boleto,), fetchone=True)
        
        if row:
            return Boleto(
                id_boleto=row[0], descricao=row[1], valor=row[2], data_vencimento=row[3], 
                id_categoria=row[4], codigo_barras=row[5], status=row[6], obs=row[7], 
                banco_pagamento=row[8]
            )
        return None

    def listar_pendentes(self) -> List[Boleto]:
        sql = """SELECT id_boleto, descricao, valor, data_vencimento, id_categoria, 
                 codigo_barras, status, obs, banco_pagamento FROM boleto WHERE status = 'pendente' 
                 ORDER BY data_vencimento ASC"""
        rows = self.__bd.executar_query(sql)
        return [Boleto(id_boleto=r[0], descricao=r[1], valor=r[2], data_vencimento=r[3], 
                       id_categoria=r[4], codigo_barras=r[5], status=r[6], obs=r[7], banco_pagamento=r[8]) for r in rows]