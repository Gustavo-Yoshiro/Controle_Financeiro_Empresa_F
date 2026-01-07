from typing import List, Dict, Optional
from datetime import datetime, date

from Persistencia.Impl import MovimentacaoImpl
from Persistencia.Entidades import Movimentacao

class FinanceiroService:
    def __init__(self):
        self.dao = MovimentacaoImpl()

    # --- MÉTODO AUXILIAR (Vindo do antigo TransacaoService) ---
    def _tratar_data(self, data_input) -> str:
        """
        Normaliza a data para string SQL (YYYY-MM-DD HH:MM:SS).
        Adiciona a hora atual para o lançamento não ficar com hora 00:00.
        """
        agora = datetime.now().time()
        
        # Se veio string (do input do usuário)
        if isinstance(data_input, str):
            try:
                # Tenta converter string simples '2023-01-01'
                data_input = datetime.strptime(data_input, "%Y-%m-%d").date()
            except:
                try:
                    # Tenta converter se já tiver hora
                    data_input = datetime.strptime(data_input, "%Y-%m-%d %H:%M:%S").date()
                except:
                    # Se falhar, usa hoje
                    data_input = date.today()
        
        # Se veio datetime object
        elif isinstance(data_input, datetime):
            data_input = data_input.date()
        
        # Se veio nulo
        elif data_input is None:
            data_input = date.today()
            
        return datetime.combine(data_input, agora).strftime("%Y-%m-%d %H:%M:%S")

    # --- REGISTRO DE TRANSAÇÕES (CORE) ---

    def registrar_gasto_manual(self, descricao: str, valor: float, id_categoria: int, 
                               data_gasto: str, banco: str, forma: str) -> str:
        try:
            # 1. Garante valor negativo
            valor_final = -abs(float(valor))
            
            # 2. Trata a data (adiciona hora)
            data_final = self._tratar_data(data_gasto)
            
            mov = Movimentacao(
                descricao=descricao,
                valor=valor_final,
                data_movimento=data_final,
                id_categoria=id_categoria,
                banco=banco,
                forma_pagamento=forma
                # Demais campos ficam None
            )
            self.dao.salvar(mov)
            return "Despesa lançada com sucesso!"
        except Exception as e:
            return f"Erro ao lançar despesa: {e}"

    def registrar_receita_manual(self, descricao: str, valor: float, id_categoria: int, 
                                 data: str, banco: str, forma: str) -> str:
        try:
            valor_final = abs(float(valor))
            data_final = self._tratar_data(data)
            
            mov = Movimentacao(
                descricao=descricao,
                valor=valor_final,
                data_movimento=data_final,
                id_categoria=id_categoria,
                banco=banco,
                forma_pagamento=forma
            )
            self.dao.salvar(mov)
            return "Receita lançada com sucesso!"
        except Exception as e:
            return f"Erro ao lançar receita: {e}"

    # --- INTEGRAÇÕES (Veículos e Imóveis) ---

    def registrar_despesa_veiculo(self, descricao: str, valor: float, id_veiculo: int, 
                                  data: str, banco: str, forma: str) -> str:
        # Categoria 3 = Manutenção Veículo
        data_final = self._tratar_data(data)
        mov = Movimentacao(
            descricao=descricao,
            valor=-abs(valor),
            data_movimento=data_final,
            id_categoria=3, 
            banco=banco,
            forma_pagamento=forma,
            id_veiculo=id_veiculo
        )
        self.dao.salvar(mov)
        return "Gasto com veículo registrado."

    def registrar_despesa_imovel(self, descricao: str, valor: float, id_kitnet: int, 
                                 data: str, banco: str, forma: str) -> str:
        # Categoria 4 = Manutenção Imóvel
        data_final = self._tratar_data(data)
        mov = Movimentacao(
            descricao=descricao,
            valor=-abs(valor),
            data_movimento=data_final,
            id_categoria=4,
            banco=banco,
            forma_pagamento=forma,
            id_kitnet=id_kitnet
        )
        self.dao.salvar(mov)
        return "Gasto com imóvel registrado."

    # --- LEITURA E ADMINISTRAÇÃO ---

    def consultar_extrato(self, data_inicio: str, data_fim: str) -> List[Dict]:
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        
        lista_formatada = []
        for m in movs:
            try:
                # Mostra apenas data DD/MM/YYYY no grid, hora fica oculta
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
        """ Calcula totais para os Cards do Dashboard """
        movs = self.dao.listar_periodo(data_inicio, data_fim)
        
        receitas = sum(m.valor for m in movs if m.valor > 0)
        despesas = sum(m.valor for m in movs if m.valor < 0)
        saldo = receitas + despesas 
        
        return {
            "receitas": receitas,
            "despesas": despesas,
            "saldo": saldo
        }
    
    def excluir_lancamento(self, id_mov: int) -> str:
        self.dao.deletar(id_mov)
        return "Lançamento excluído."
    
    # Adicionar no FinanceiroService.py se não tiver:
    def admin_editar_movimentacao(self, id_mov, desc, valor, data, banco):
        mov = self.dao.buscar_por_id(id_mov)
        if mov:
            mov.descricao = desc
            mov.valor = valor
            mov.data_movimento = self._tratar_data(data) # Usa aquele método auxiliar
            mov.banco = banco
            self.dao.salvar(mov)