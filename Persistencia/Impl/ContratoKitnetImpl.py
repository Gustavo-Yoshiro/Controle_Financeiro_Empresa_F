from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades.ContratoKitnet import ContratoKitnet

class ContratoKitnetImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, contrato: ContratoKitnet) -> int:
        sql = """
            INSERT INTO contrato_kitnet 
            (id_kitnet, id_inquilino, valor_fechado, data_vencimento, data_inicio, data_fim, ativo, mobiliado, obs_mobiliado, pdf_caminho_contrato_kit) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros = (
            contrato.id_kitnet, 
            contrato.id_inquilino, 
            contrato.valor_fechado, 
            contrato.data_vencimento, 
            contrato.data_inicio, 
            contrato.data_fim, 
            contrato.ativo, 
            contrato.mobiliado, 
            contrato.obs_mobiliado, 
            contrato.pdf_caminho
        )
        id_gerado = self.__bd.executar(sql, parametros)
        contrato.id_contrato_kitnet = id_gerado
        return id_gerado

    def atualizar(self, contrato: ContratoKitnet) -> None:
        sql = """
            UPDATE contrato_kitnet 
            SET id_kitnet=?, id_inquilino=?, valor_fechado=?, data_vencimento=?, 
                data_inicio=?, data_fim=?, ativo=?, mobiliado=?, obs_mobiliado=?, pdf_caminho_contrato_kit=? 
            WHERE id_contrato_kitnet=?
        """
        parametros = (
            contrato.id_kitnet, 
            contrato.id_inquilino, 
            contrato.valor_fechado, 
            contrato.data_vencimento, 
            contrato.data_inicio, 
            contrato.data_fim, 
            contrato.ativo, 
            contrato.mobiliado, 
            contrato.obs_mobiliado, 
            contrato.pdf_caminho, 
            contrato.id_contrato_kitnet
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_contrato: int) -> None:
        sql = "DELETE FROM contrato_kitnet WHERE id_contrato_kitnet = ?"
        self.__bd.executar(sql, (id_contrato,))

    def listar_ativos(self) -> List[ContratoKitnet]:
        # Traz apenas os contratos que estão valendo (Ativo = 1)
        sql = """
            SELECT id_contrato_kitnet, id_kitnet, id_inquilino, valor_fechado, data_vencimento, 
                   data_inicio, data_fim, ativo, mobiliado, obs_mobiliado, pdf_caminho_contrato_kit 
            FROM contrato_kitnet 
            WHERE ativo = 1
        """
        rows = self.__bd.executar_query(sql)
        
        return [
            ContratoKitnet(
                id_contrato_kitnet=r[0], id_kitnet=r[1], id_inquilino=r[2], 
                valor_fechado=r[3], data_vencimento=r[4], data_inicio=r[5], 
                data_fim=r[6], ativo=r[7], mobiliado=r[8], 
                obs_mobiliado=r[9], pdf_caminho=r[10]
            ) for r in rows
        ]