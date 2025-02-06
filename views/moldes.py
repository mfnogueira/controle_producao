import streamlit as st
import pandas as pd
from datetime import datetime, date
from models.molde import Molde
from database.connection import DatabaseError, get_table_download_link

def render_moldes_view():
    st.title("🔧 Cadastro de Moldes")
    
    tab1, tab2, tab3 = st.tabs(["Cadastro", "Visualização", "Manutenção"])
    
    with tab1:
        with st.form("form_molde"):
            st.subheader("Novo Molde")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome do Molde")
                fabricante = st.text_input("Fabricante")
                num_cavidades = st.number_input(
                    "Número de Cavidades",
                    min_value=1,
                    value=1
                )
            
            with col2:
                ciclos_manutencao = st.number_input(
                    "Ciclos até Manutenção",
                    min_value=1000,
                    value=10000,
                    step=1000,
                    help="Número de ciclos até necessitar manutenção preventiva"
                )
            
            observacoes = st.text_area("Observações")
            
            submitted = st.form_submit_button(
                "Cadastrar Molde",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                try:
                    st.info(f"Tentando cadastrar molde: {nome}")
                    molde = Molde.criar(
                        nome=nome,
                        fabricante=fabricante,
                        num_cavidades=num_cavidades,
                        manutencao_proxima=ciclos_manutencao,
                        observacoes=observacoes
                    )
                    molde.salvar()
                    st.success("✅ Molde cadastrado com sucesso!")
                    st.info(f"ID do molde cadastrado: {molde.id}")
                except (ValueError, DatabaseError) as e:
                    st.error(f"❌ Erro ao cadastrar: {str(e)}")
    
    with tab2:
        st.subheader("Moldes Cadastrados")
        
        try:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_status = st.selectbox(
                    "Status",
                    ["Todos", "Disponível", "Em Uso", "Manutenção"]
                )
            with col2:
                filtro_cavidades = st.number_input(
                    "Mínimo de Cavidades",
                    min_value=1,
                    value=1
                )
            with col3:
                filtro_fabricante = st.text_input("Fabricante")
            
            # Buscar dados
            st.info("Buscando moldes...")
            moldes = Molde.get_todos()
            st.info(f"Total de moldes encontrados: {len(moldes)}")
            
            # Debug: mostrar dados brutos
            if st.checkbox("Mostrar dados brutos"):
                for m in moldes:
                    st.write(m)
            
            # Aplicar filtros
            if filtro_status != "Todos":
                moldes = [m for m in moldes if m.status == filtro_status]
            if filtro_cavidades > 1:
                moldes = [m for m in moldes if m.num_cavidades >= filtro_cavidades]
            if filtro_fabricante:
                moldes = [m for m in moldes if filtro_fabricante.lower() in m.fabricante.lower()]
            
            if moldes:
                # Converter para DataFrame
                df = pd.DataFrame([{
                    'Nome': m.nome,
                    'Fabricante': m.fabricante,
                    'Cavidades': m.num_cavidades,
                    'Ciclos Totais': m.ciclos_total,
                    'Ciclos desde Manutenção': m.ciclos_desde_manutencao,
                    'Próxima Manutenção em': m.manutencao_proxima,
                    'Status': m.status,
                    'Observações': m.observacoes
                } for m in moldes])
                
                # Adicionar coluna de progresso até manutenção
                df['Progresso Manutenção (%)'] = df.apply(
                    lambda x: min(100, round(x['Ciclos desde Manutenção'] / x['Próxima Manutenção em'] * 100, 1))
                    if x['Próxima Manutenção em'] else 0,
                    axis=1
                )
                
                # Mostrar tabela
                st.dataframe(df)
                
                # Botão de download
                st.markdown(
                    get_table_download_link(df, "moldes"),
                    unsafe_allow_html=True
                )
            else:
                st.info("Nenhum molde cadastrado ou encontrado com os filtros")
        except Exception as e:
            st.error(f"Erro ao buscar moldes: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    with tab3:
        st.subheader("Registro de Manutenção")