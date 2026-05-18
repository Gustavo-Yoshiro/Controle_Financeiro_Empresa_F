from typing import List, Dict, Optional
from datetime import datetime, date

from Persistencia.Impl import MovimentacaoImpl
from Persistencia.Entidades import Movimentacao

class FinanceiroService:
    def __init__(self):
        self.dao = MovimentacaoImpl()

    def _tratar_data(self, data_input) -> str:
        """
        Normaliza a data para string SQL (YYYY-MM-DD HH:MM:SS).
        Adiciona a hora atual para o lançamento não ficar com hora 00:00.
        """
        agora = datetime.now().time()
        
        if isinstance(data_input, str):
            try:
                data_input = datetime.strptime(data_input, "%Y-%m-%d").date()
            except:
                try:
                    data_input = datetime.strptime(data_input, "%Y-%m-%d %H:%M:%S").date()
                except:
                    data_input = date.today()
        
        elif isinstance(data_input, datetime):
            data_input = data_input.date()
        elif data_input is None:
            data_input = date.today()
            
        return datetime.combine(data_input, agora).strftime("%Y-%m-%d %H:%M:%S")

    def get_saldo_atual(self) -> float:
        """Calcula quanto tem de dinheiro real no banco agora"""
        movs = self.dao.listar_periodo("2000-01-01", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        receitas = sum(m.valor for m in movs if m.valor > 0)
        despesas = sum(m.valor for m in movs if m.valor < 0)
        return receitas + despesas


    def registrar_gasto_manual(self, descricao: str, valor: float, id_categoria: int, 
                               data_gasto: str, banco: str, forma: str,
                               id_veiculo: int = None, id_divida_veiculo: int = None,
                               permitir_negativo: bool = False) -> Dict: 
        try:
            valor_abs = abs(float(valor))
            valor_final = -valor_abs
            
            if forma != "Crédito":
                saldo_atual = self.get_saldo_atual()
                if saldo_atual < valor_abs and not permitir_negativo:
                    return {
                        "sucesso": False, 
                        "msg": f"🚫 Saldo Insuficiente! Você tem R$ {saldo_atual:.2f} e quer gastar R$ {valor_abs:.2f}. Marque 'Permitir Negativo' se for cheque especial."
                    }

            data_final = self._tratar_data(data_gasto)
            
            mov = Movimentacao(
                descricao=descricao,
                valor=valor_final,
                data_movimento=data_final,
                id_categoria=id_categoria,
                banco=banco,
                forma_pagamento=forma,
                id_veiculo=id_veiculo,
                id_divida_veiculo=id_divida_veiculo
            )
            self.dao.salvar(mov)
            return {"sucesso": True, "msg": "Despesa lançada com sucesso!"}
        except Exception as e:
            return {"sucesso": False, "msg": f"Erro ao lançar despesa: {e}"}

    def registrar_receita_manual(self, descricao: str, valor: float, id_categoria: int, 
                                 data: str, banco: str, forma: str,
                                 id_kitnet: int = None, 
                                 id_pagamento_aluguel: int = None,
                                 id_pagamento_alocacao: int = None) -> Dict:
        try:
            valor_final = abs(float(valor))
            data_final = self._tratar_data(data)
            
            mov = Movimentacao(
                descricao=descricao,
                valor=valor_final,
                data_movimento=data_final,
                id_categoria=id_categoria,
                banco=banco,
                forma_pagamento=forma,
                id_kitnet=id_kitnet,
                id_pagamento_aluguel=id_pagamento_aluguel,
                id_pagamento_alocacao=id_pagamento_alocacao
            )
            self.dao.salvar(mov)
            return {"sucesso": True, "msg": "Receita lançada com sucesso!"}
        except Exception as e:
            return {"sucesso": False, "msg": f"Erro ao lançar receita: {e}"}

    
    def registrar_despesa_veiculo(self, descricao: str, valor: float, id_veiculo: int, 
                                  data: str, banco: str, forma: str) -> str:
        res = self.registrar_gasto_manual(
            descricao=descricao, valor=valor, id_categoria=3, 
            data_gasto=data, banco=banco, forma=forma, id_veiculo=id_veiculo
        )
        return res["msg"]

    def registrar_despesa_imovel(self, descricao: str, valor: float, 
                                 id_kitnet: int = None, bloco_alvo: str = None,     
                                 data: str = None, banco: str = "Dinheiro", forma: str = "Dinheiro") -> str:
        try:
            data_final = self._tratar_data(data)
            mov = Movimentacao(
                descricao=descricao,
                valor=-abs(float(valor)),
                data_movimento=data_final,
                id_categoria=4, 
                banco=banco,
                forma_pagamento=forma,
                id_kitnet=id_kitnet, 
                identificador_bloco=bloco_alvo
            )
            self.dao.salvar(mov)
            return "Gasto com imóvel registrado."
        except Exception as e:
            return f"Erro: {e}"


    def consultar_extrato(self, data_inicio: str, data_fim: str) -> List[Dict]:
        """ Usado pelo RelatorioService ou visualizações simples """
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        
        lista_formatada = []
        for m in movs:
            try:
                dt_obj = datetime.strptime(str(m.data_movimento), "%Y-%m-%d %H:%M:%S")
                data_br = dt_obj.strftime("%d/%m/%Y")
            except:
                data_br = str(m.data_movimento)

            lista_formatada.append({
                "ID": m.id_movimentacao,
                "Data": data_br,
                "Descrição": m.descricao,
                "Categoria": m.id_categoria, 
                "Banco": m.banco,
                "Valor": m.valor
            })
        return lista_formatada

    def calcular_kpis(self, data_inicio: str, data_fim: str) -> Dict:
        """ Mantido para compatibilidade com Dashboard antigo """
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        receitas = sum(m.valor for m in movs if m.valor > 0)
        despesas = sum(m.valor for m in movs if m.valor < 0)
        saldo = receitas + despesas 
        return {"receitas": receitas, "despesas": despesas, "saldo": saldo}


    def gerar_extrato_detalhado(self, data_inicio: str, data_fim: str) -> List[Dict]:
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        return [{
            "id": m.id_movimentacao, "data": m.data_movimento, "descricao": m.descricao,
            "valor": m.valor, "banco": m.banco, "categoria": m.id_categoria
        } for m in movs]

    def admin_buscar_movimentacao(self, id_mov: int) -> Optional[Movimentacao]:
        return self.dao.buscar_por_id(id_mov)

    def admin_editar_movimentacao(self, id_mov, desc, valor, data, banco):
        mov = self.dao.buscar_por_id(id_mov)
        if mov:
            mov.descricao = desc
            mov.valor = valor
            mov.data_movimento = self._tratar_data(data)
            mov.banco = banco
            self.dao.salvar(mov)

    def admin_excluir_movimentacao(self, id_mov: int) -> str:
        self.dao.deletar(id_mov)
        return "Lançamento excluído."

    def excluir_lancamento(self, id_mov: int) -> str:
        return self.admin_excluir_movimentacao(id_mov)