from typing import List, Optional
from Persistencia.Banco import BancoDeDados
from Persistencia.Entidades import ContratoKitnet

class ContratoKitnetImpl:
    def __init__(self):
        self.__bd = BancoDeDados()

    def salvar(self, contrato: ContratoKitnet) -> int:
        # Se tem ID, atualiza. Se não, cria.
        if contrato.id_contrato_kitnet:
            self.atualizar(contrato)
            return contrato.id_contrato_kitnet
        else:
            # ADICIONADO: valor_esgoto_padrao no INSERT
            sql = """
                INSERT INTO contrato_kitnet 
                (id_kitnet, id_inquilino, valor_fechado, valor_esgoto_padrao, data_vencimento, 
                 data_inicio, data_fim, ativo, mobiliado, obs_mobiliado, pdf_caminho_contrato_kit) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            parametros = (
                contrato.id_kitnet, 
                contrato.id_inquilino, 
                contrato.valor_fechado, 
                contrato.valor_esgoto_padrao, # <--- Novo
                contrato.data_vencimento, 
                contrato.data_inicio, 
                contrato.data_fim, 
                contrato.ativo, 
                contrato.mobiliado, 
                contrato.obs_mobiliado, 
                contrato.pdf_caminho_contrato_kit 
            )
            id_gerado = self.__bd.executar(sql, parametros)
            contrato.id_contrato_kitnet = id_gerado
            return id_gerado

    def atualizar(self, contrato: ContratoKitnet) -> None:
        # ADICIONADO: valor_esgoto_padrao no UPDATE
        sql = """
            UPDATE contrato_kitnet 
            SET id_kitnet=?, id_inquilino=?, valor_fechado=?, valor_esgoto_padrao=?, 
                data_vencimento=?, data_inicio=?, data_fim=?, ativo=?, 
                mobiliado=?, obs_mobiliado=?, pdf_caminho_contrato_kit=? 
            WHERE id_contrato_kitnet=?
        """
        parametros = (
            contrato.id_kitnet, 
            contrato.id_inquilino, 
            contrato.valor_fechado, 
            contrato.valor_esgoto_padrao, # <--- Novo
            contrato.data_vencimento, 
            contrato.data_inicio, 
            contrato.data_fim, 
            contrato.ativo, 
            contrato.mobiliado, 
            contrato.obs_mobiliado, 
            contrato.pdf_caminho_contrato_kit, 
            contrato.id_contrato_kitnet
        )
        self.__bd.executar(sql, parametros)

    def deletar(self, id_contrato: int) -> None:
        sql = "DELETE FROM contrato_kitnet WHERE id_contrato_kitnet = ?"
        self.__bd.executar(sql, (id_contrato,))

    def listar_ativos(self) -> List[ContratoKitnet]:
        # ADICIONADO: valor_esgoto_padrao no SELECT
        sql = """
            SELECT id_contrato_kitnet, id_kitnet, id_inquilino, valor_fechado, valor_esgoto_padrao,
                   data_vencimento, data_inicio, data_fim, ativo, mobiliado, 
                   obs_mobiliado, pdf_caminho_contrato_kit 
            FROM contrato_kitnet 
            WHERE ativo = 1
        """
        rows = self.__bd.executar_query(sql)
        
        # Mapeamento atualizado com os novos índices
        return [
            ContratoKitnet(
                id_contrato_kitnet=r[0], 
                id_kitnet=r[1], 
                id_inquilino=r[2], 
                valor_fechado=r[3], 
                valor_esgoto_padrao=r[4], # <--- Novo índice 4
                data_vencimento=r[5], 
                data_inicio=r[6], 
                data_fim=r[7], 
                ativo=r[8], 
                mobiliado=r[9], 
                obs_mobiliado=r[10], 
                pdf_caminho_contrato_kit=r[11]
            ) for r in rows
        ]
    
    def buscar_por_id(self, id_contrato: int) -> Optional[ContratoKitnet]:
        # ADICIONADO: valor_esgoto_padrao no SELECT
        sql = """
            SELECT id_contrato_kitnet, id_kitnet, id_inquilino, valor_fechado, valor_esgoto_padrao,
                   data_vencimento, data_inicio, data_fim, ativo, mobiliado, 
                   obs_mobiliado, pdf_caminho_contrato_kit 
            FROM contrato_kitnet 
            WHERE id_contrato_kitnet = ?
        """
        row = self.__bd.executar_query(sql, (id_contrato,), fetchone=True)
        
        if row:
            return ContratoKitnet(
                id_contrato_kitnet=row[0], 
                id_kitnet=row[1], 
                id_inquilino=row[2], 
                valor_fechado=row[3], 
                valor_esgoto_padrao=row[4], # <--- Novo índice 4
                data_vencimento=row[5], 
                data_inicio=row[6], 
                data_fim=row[7], 
                ativo=row[8], 
                mobiliado=row[9], 
                obs_mobiliado=row[10], 
                pdf_caminho_contrato_kit=row[11] 
            )
        return None