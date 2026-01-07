import streamlit as st
import pandas as pd
from datetime import date, datetime

class ConfiguracoesPage:
    def __init__(self, config_service, kitnet_service, inquilino_service, financeiro_service, 
                 transporte_service, pix_service, boleto_service, emprestimo_service):
        self.cfg = config_service
        self.kit = kitnet_service
        self.inq = inquilino_service 
        self.fin = financeiro_service
        self.trans = transporte_service
        self.pix = pix_service
        self.bol = boleto_service
        self.emp = emprestimo_service

    def render(self):
        st.title("⚙️ Painel de Controle e Correções")

        # Criação das Abas
        tab_geral, tab_pix, tab_kit, tab_inq, tab_veic, tab_fin, tab_div = st.tabs([
            "🏦 Geral", 
            "💠 Pix", 
            "🏠 Kitnets", 
            "👤 Inquilinos", 
            "🚚 Veículos",
            "💰 Extrato",
            "📑 Dívidas"
        ])

        # =====================================================================
        # 1. GERAL (BANCOS E CATEGORIAS)
        # =====================================================================
        with tab_geral:
            st.subheader("Cadastros Básicos")
            
            c1, c2 = st.columns(2)
            
            # --- BANCOS ---
            with c1:
                with st.expander("Gerenciar Bancos"):
                    # Adicionar
                    novo_banco = st.text_input("Adicionar Novo Banco")
                    if st.button("Salvar Banco"):
                        st.success(self.cfg.adicionar_banco(novo_banco))
                        st.rerun()
                    
                    st.divider()
                    
                    # Editar / Excluir
                    bancos = self.cfg.listar_bancos()
                    b_sel = st.selectbox("Selecione para Editar", bancos)
                    if b_sel:
                        renomear = st.text_input("Renomear para", value=b_sel)
                        
                        b1, b2 = st.columns(2)
                        if b1.button("💾 Renomear"):
                            st.success(self.cfg.editar_banco(b_sel, renomear))
                            st.rerun()
                        if b2.button("🗑️ Excluir"):
                            msg = self.cfg.excluir_banco(b_sel)
                            if "sucesso" in msg: st.success(msg); st.rerun()
                            else: st.error(msg)

            # --- CATEGORIAS ---
            with c2:
                with st.expander("Gerenciar Categorias"):
                    # Adicionar
                    nc_nome = st.text_input("Nova Categoria")
                    nc_tipo = st.selectbox("Tipo", ["receita", "despesa"])
                    if st.button("Criar Categoria"):
                        self.cfg.adicionar_categoria(nc_nome, nc_tipo)
                        st.success("Criado!")
                        st.rerun()
                    
                    st.divider()
                    
                    # Editar / Excluir
                    cats = self.cfg.listar_categorias()
                    if cats:
                        map_c = {f"{c['nome']} ({c['tipo']})": c['id'] for c in cats}
                        c_sel_nome = st.selectbox("Editar Categoria", list(map_c.keys()))
                        c_id = map_c[c_sel_nome]
                        
                        # Limpa string para edição
                        nome_limpo = c_sel_nome.split(" (")[0]
                        renomear_c = st.text_input("Novo Nome", value=nome_limpo)
                        
                        bt1, bt2 = st.columns(2)
                        if bt1.button("Salvar Cat."):
                            self.cfg.editar_categoria(c_id, renomear_c)
                            st.success("Salvo!")
                            st.rerun()
                        if bt2.button("Excluir Cat."):
                            msg = self.cfg.excluir_categoria(c_id)
                            if "removida" in msg: st.success(msg); st.rerun()
                            else: st.error(msg)

        # =====================================================================
        # 2. PIX
        # =====================================================================
        with tab_pix:
            st.subheader("Gerenciar Chaves PIX")
            
            with st.expander("➕ Nova Chave", expanded=False):
                with st.form("add_pix_form"):
                    c1, c2 = st.columns(2)
                    titulo = c1.text_input("Título (Ex: Pix Loja)")
                    chave = c2.text_input("Chave Pix")
                    
                    c3, c4, c5 = st.columns(3)
                    tipo = c3.selectbox("Tipo", ["CPF", "CNPJ", "Celular", "Email", "Aleatória"])
                    lista_bancos = self.cfg.listar_bancos()
                    banco = c4.selectbox("Banco", lista_bancos)
                    titular = c5.text_input("Titular")
                    
                    if st.form_submit_button("Salvar Chave"):
                        self.pix.cadastrar_pix(titulo, chave, tipo, titular, banco)
                        st.success("Salvo!")
                        st.rerun()
            
            st.divider()
            
            pix_list = self.pix.listar_pix()
            if not pix_list:
                st.info("Nenhuma chave cadastrada.")
            else:
                map_pix = {f"{p.titulo} ({p.banco}) - {p.chave}": p.id_pix for p in pix_list}
                sel_pix_txt = st.selectbox("Selecione para Editar/Excluir:", list(map_pix.keys()))
                id_pix_sel = map_pix[sel_pix_txt]
                
                obj_pix = self.pix.buscar_por_id(id_pix_sel)
                
                if obj_pix:
                    with st.form("edit_pix_form"):
                        nc1, nc2 = st.columns(2)
                        n_titulo = nc1.text_input("Título", value=obj_pix.titulo)
                        n_chave = nc2.text_input("Chave", value=obj_pix.chave)
                        
                        nc3, nc4, nc5 = st.columns(3)
                        
                        tipos_opts = ["CPF", "CNPJ", "Celular", "Email", "Aleatória"]
                        idx_tipo = tipos_opts.index(obj_pix.tipo) if obj_pix.tipo in tipos_opts else 0
                        n_tipo = nc3.selectbox("Tipo", tipos_opts, index=idx_tipo, key="ept")
                        
                        idx_banco = lista_bancos.index(obj_pix.banco) if obj_pix.banco in lista_bancos else 0
                        n_banco = nc4.selectbox("Banco", lista_bancos, index=idx_banco, key="epb")
                        
                        n_titular = nc5.text_input("Titular", value=obj_pix.titular)
                        is_fav = st.checkbox("⭐ Favorito?", value=bool(obj_pix.favorito))

                        col_s, col_d = st.columns(2)
                        if col_s.form_submit_button("💾 Salvar Alterações"):
                            self.pix.editar_pix(obj_pix.id_pix, n_titulo, n_chave, n_tipo, n_titular, n_banco)
                            fav_int = 1 if is_fav else 0
                            if fav_int != obj_pix.favorito:
                                self.pix.alternar_favorito(obj_pix.id_pix, fav_int)
                            
                            st.success("Atualizado!")
                            st.rerun()
                            
                        if col_d.form_submit_button("🗑️ Excluir Chave"):
                            self.pix.excluir_pix(obj_pix.id_pix)
                            st.success("Removido!")
                            st.rerun()

        # =====================================================================
        # 3. KITNETS
        # =====================================================================
        with tab_kit:
            st.subheader("Corrigir Kitnets")
            
            lista_kits = self.kit.admin_listar_todas() 
            if not lista_kits:
                st.warning("Sem kitnets.")
            else:
                map_k = {f"{k.identificador}-{k.numero} (ID: {k.id_kitnet})": k for k in lista_kits}
                sel_k_nome = st.selectbox("Selecione Kitnet", list(map_k.keys()))
                obj_k = map_k[sel_k_nome]

                with st.form("edit_kit_form"):
                    c1, c2 = st.columns(2)
                    
                    opts_ident = ["M1", "M2", "K", "Casa", "Apto"]
                    idx_ident = opts_ident.index(obj_k.identificador) if obj_k.identificador in opts_ident else 0
                    novo_ident = c1.selectbox("Identificador", opts_ident, index=idx_ident)
                    
                    novo_num = c2.number_input("Número", value=obj_k.numero)
                    novo_val = st.number_input("Preço Padrão", value=obj_k.preco_padrao)
                    
                    novo_quartos = st.number_input("Quartos", value=obj_k.quartos, min_value=1)

                    opts_st = ["LIVRE", "OCUPADA", "MANUTENCAO"]
                    idx_st = opts_st.index(obj_k.status) if obj_k.status in opts_st else 0
                    novo_st = st.selectbox("Status", opts_st, index=idx_st)

                    col_ks, col_kd = st.columns(2)
                    if col_ks.form_submit_button("Salvar Kitnet"):
                        msg = self.kit.admin_editar(obj_k.id_kitnet, novo_num, novo_ident, novo_val, novo_st, novo_quartos)
                        st.success(msg)
                        st.rerun()
                    
                    if col_kd.form_submit_button("Excluir Kitnet"):
                        msg = self.kit.admin_excluir(obj_k.id_kitnet)
                        if "Erro" in msg: st.error(msg)
                        else: st.success(msg); st.rerun()

        # =====================================================================
        # 4. INQUILINOS
        # =====================================================================
        with tab_inq:
            st.subheader("Corrigir Inquilinos")
            inqs = self.inq.admin_listar_todos()
            
            if inqs:
                map_i = {f"{i.nome} (CPF: {i.cpf})": i for i in inqs}
                sel_i = st.selectbox("Selecione Inquilino", list(map_i.keys()))
                obj_i = map_i[sel_i]

                with st.form("edit_inq_form"):
                    nn = st.text_input("Nome", value=obj_i.nome)
                    ncpf = st.text_input("CPF", value=obj_i.cpf)
                    ntel = st.text_input("Telefone", value=obj_i.telefone)
                    nemail = st.text_input("Email", value=obj_i.email or "")
                    
                    # Campos extras
                    nprof = st.text_input("Profissão", value=obj_i.profissao or "")
                    nobs = st.text_area("Obs", value=obj_i.obs or "")
                    
                    if st.form_submit_button("Atualizar Inquilino"):
                        # Passando todos os campos requeridos
                        self.inq.admin_editar(obj_i.id_inquilino, nn, ncpf, ntel, obj_i.sexo, obj_i.estado_civil, nprof, nemail, nobs)
                        st.success("Atualizado!")
                        st.rerun()
            else:
                st.info("Nenhum inquilino cadastrado.")

        # =====================================================================
        # 5. VEÍCULOS
        # =====================================================================
        # =====================================================================
        # 5. VEÍCULOS (CORRIGIDO)
        # =====================================================================
        with tab_veic:
            st.subheader("Editar Frota")
            # CORREÇÃO 1: Nome do método ajustado para o padrão do Service
            veics = self.trans.admin_listar_todos()
            
            if veics:
                map_v = {f"{v.modelo} - {v.placa}": v for v in veics}
                sel_v = st.selectbox("Selecione Veículo", list(map_v.keys()))
                obj_v = map_v[sel_v]
                
                with st.form("edit_veic_form"):
                    nm = st.text_input("Modelo", value=obj_v.modelo)
                    np = st.text_input("Placa", value=obj_v.placa)
                    
                    nano = st.number_input("Ano", value=obj_v.ano)
                    nfin = st.text_input("Finalidade", value=obj_v.finalidade)
                    
                    opts_v = ["ativo", "alocado", "manutencao"]
                    # Tratamento seguro para índice
                    idx_v = opts_v.index(obj_v.status) if obj_v.status in opts_v else 0
                    nst = st.selectbox("Status", opts_v, index=idx_v)
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Salvar Veículo"):
                        # CORREÇÃO 2: Nome do método ajustado (admin_editar)
                        self.trans.admin_editar(obj_v.id_veiculo, nm, np, nano, nfin, nst)
                        st.success("Veículo atualizado!")
                        st.rerun()
                        
                    if c2.form_submit_button("🗑️ Excluir Veículo"):
                        # CORREÇÃO 3: Nome do método ajustado (admin_excluir)
                        self.trans.admin_excluir(obj_v.id_veiculo)
                        st.success("Veículo excluído!")
                        st.rerun()
            else:
                st.info("Sem veículos.")

        # =====================================================================
        # 6. TRANSAÇÕES
        # =====================================================================
        with tab_fin:
            st.subheader("✏️ Corrigir Lançamento no Extrato")
            st.info("Filtre pela data, selecione a transação e corrija o valor ou descrição.")
            
            c_f1, c_f2 = st.columns(2)
            d_ini = c_f1.date_input("De", value=date.today())
            d_fim = c_f2.date_input("Até", value=date.today())
            
            movs = self.fin.consultar_extrato(str(d_ini), str(d_fim))
            
            if not movs:
                st.warning("Nenhuma transação neste período.")
            else:
                map_mov = {f"[{m['Data']}] {m['Descrição']} (R$ {m['Valor']})": m['ID'] for m in movs}
                sel_mov_txt = st.selectbox("Escolha a transação:", list(map_mov.keys()))
                id_mov_sel = map_mov[sel_mov_txt]
                
                # Busca via DAO direto (Acesso seguro pois service expõe dao)
                # Ou idealmente criar self.fin.buscar_por_id(id)
                obj_mov = self.fin.dao.buscar_por_id(id_mov_sel)
                
                if obj_mov:
                    st.divider()
                    with st.form("form_edit_fin"):
                        st.write(f"ID: {obj_mov.id_movimentacao}")
                        n_desc = st.text_input("Descrição", value=obj_mov.descricao)
                        n_val = st.number_input("Valor (Negativo=Gasto)", value=float(obj_mov.valor))
                        
                        # Data
                        val_data = obj_mov.data_movimento
                        if isinstance(val_data, str):
                            try: val_data = datetime.strptime(val_data, "%Y-%m-%d %H:%M:%S").date()
                            except: val_data = date.today()
                        n_data = st.date_input("Data", value=val_data)
                        
                        # Banco
                        lista_bancos = self.cfg.listar_bancos()
                        idx_banco = lista_bancos.index(obj_mov.banco) if obj_mov.banco in lista_bancos else 0
                        n_banco = st.selectbox("Banco", lista_bancos, index=idx_banco, key="mov_banco")
                        
                        c_save, c_del = st.columns(2)
                        
                        if c_save.form_submit_button("✅ Salvar Correção"):
                            # Certifique-se que este método existe no FinanceiroService
                            try:
                                self.fin.admin_editar_movimentacao(obj_mov.id_movimentacao, n_desc, n_val, str(n_data), n_banco)
                                st.success("Transação corrigida!")
                                st.rerun()
                            except AttributeError:
                                st.error("Erro: Método 'admin_editar_movimentacao' não encontrado no FinanceiroService.")
                            
                        if c_del.form_submit_button("🗑️ Apagar Transação"):
                            self.fin.excluir_lancamento(obj_mov.id_movimentacao)
                            st.error("Transação apagada.")
                            st.rerun()

        # =====================================================================
        # 7. DÍVIDAS
        # =====================================================================
        with tab_div:
            c_bol, c_emp = st.columns(2)
            
            with c_bol:
                st.subheader("Corrigir Boletos")
                todos_bol = self.bol.admin_listar_todos()
                if todos_bol:
                    map_b = {f"{b.descricao} (R$ {b.valor})": b.id_boleto for b in todos_bol}
                    sel_b = st.selectbox("Selecione Boleto", list(map_b.keys()))
                    obj_b = next(b for b in todos_bol if b.id_boleto == map_b[sel_b])
                    
                    with st.form("ed_bol_form"):
                        d = st.text_input("Desc", obj_b.descricao)
                        v = st.number_input("Valor", value=obj_b.valor)
                        dt = st.text_input("Vencimento", obj_b.data_vencimento)
                        
                        idx_sb = 0 if obj_b.status == "pendente" else 1
                        stt = st.selectbox("Status", ["pendente", "pago"], index=idx_sb)
                        
                        if st.form_submit_button("Salvar Boleto"):
                            self.bol.admin_editar(obj_b.id_boleto, d, v, dt, stt, obj_b.banco_pagamento)
                            st.success("Salvo!")
                            st.rerun()
                        if st.form_submit_button("Excluir Boleto"):
                            self.bol.admin_excluir(obj_b.id_boleto)
                            st.rerun()
                else:
                    st.info("Sem boletos.")

            with c_emp:
                st.subheader("Corrigir Empréstimos")
                emps = self.emp.listar_emprestimos()
                if emps:
                    map_e = {f"{e.descricao} (Total: {e.valor_total})": e for e in emps}
                    sel_e = st.selectbox("Selecione Empréstimo", list(map_e.keys()))
                    obj_e = map_e[sel_e]
                    
                    with st.form("ed_emp_form"):
                        d = st.text_input("Desc", obj_e.descricao)
                        v = st.number_input("Total", value=obj_e.valor_total)
                        
                        idx_se = 0 if obj_e.status == "ativo" else 1
                        s = st.selectbox("Status", ["ativo", "quitado"], index=idx_se)
                        
                        if st.form_submit_button("Salvar Empréstimo"):
                            self.emp.admin_editar(obj_e.id_emprestimo, d, v, s)
                            st.success("Salvo")
                            st.rerun()
                        if st.form_submit_button("Excluir Empréstimo"):
                            self.emp.admin_excluir(obj_e.id_emprestimo)
                            st.rerun()
                else:
                    st.info("Sem empréstimos.")