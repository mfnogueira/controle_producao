import streamlit as st
import pandas as pd
from datetime import datetime, date
from models.injetora import Injetora
from utils.formatters import format_decimal
from database.connection import DatabaseError, get_table_download_link

def render_injetoras_view():
    st.title("📦 Cadastro de Injetoras")
    
    tab1, tab2, tab3 = st.tabs(["Cadastro", "Visualização", "Manutenção"])
    
    with tab1:
        with st.form("form_injetora"):
            st.subheader("Nova Injetora")
            
            col1, col2 = st.columns(2)
            
            with col1:
                numero = st.text_input("Número da Injetora")
                marca = st.text_input("Marca")
                capacidade = st.number_input(
                    "Capacidade (toneladas)",
                    min_value=0.0,
                    step=0.1
                )
            
            with col2:
                manutencao_proxima = st.date_input(
                    "Próxima Manutenção Preventiva",
                    min_value=date.today()
                )
                horimetro = st.number_input(
                    "Horímetro Atual",
                    min_value=0
                )
                horimetro_proxima = st.number_input(
                    "Horímetro Próxima Manutenção",
                    min_value=horimetro
                )
            
            observacoes = st.text_area("Observações")
            
            submitted = st.form_submit_button(
                "Cadastrar Injetora",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                try:
                    st.info(f"Tentando cadastrar injetora: {numero}")
                    injetora = Injetora.criar(
                        numero=numero,
                        marca=marca,
                        capacidade_ton=capacidade,
                        manutencao_proxima=manutencao_proxima,
                        horimetro_proxima_manutencao=horimetro_proxima,
                        observacoes=observacoes
                    )
                    injetora.horimetro_atual = horimetro
                    injetora.salvar()
                    st.success("✅ Injetora cadastrada com sucesso!")
                    st.info(f"ID da injetora cadastrada: {injetora.id}")
                except (ValueError, DatabaseError) as e:
                    st.error(f"❌ Erro ao cadastrar: {str(e)}")
    
    with tab2:
        st.subheader("Injetoras Cadastradas")
        
        try:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_status = st.selectbox(
                    "Status",
                    ["Todos", "Disponível", "Em Uso", "Manutenção"]
                )
            with col2:
                filtro_capacidade = st.number_input(
                    "Capacidade Mínima (ton)",
                    min_value=0.0,
                    value=0.0
                )
            
            # Buscar dados
            st.info("Buscando injetoras...")
            injetoras = Injetora.get_todos()
            st.info(f"Total de injetoras encontradas: {len(injetoras)}")
            
            # Debug: mostrar dados brutos
            if st.checkbox("Mostrar dados brutos"):
                for i in injetoras:
                    st.write(i)
            
            # Aplicar filtros
            if filtro_status != "Todos":
                injetoras = [i for i in injetoras if i.status == filtro_status]
            if filtro_capacidade > 0:
                injetoras = [i for i in injetoras if i.capacidade_ton >= filtro_capacidade]
            
            if injetoras:
                # Converter para DataFrame
                df = pd.DataFrame([{
                    'Número': i.numero,
                    'Marca': i.marca,
                    'Capacidade (ton)': i.capacidade_ton,
                    'Status': i.status,
                    'Próxima Manutenção': i.manutencao_proxima,
                    'Horímetro': i.horimetro_atual,
                    'Observações': i.observacoes
                } for i in injetoras])
                
                # Mostrar tabela
                st.dataframe(df)
                
                # Botão de download
                st.markdown(
                    get_table_download_link(df, "injetoras"),
                    unsafe_allow_html=True
                )
            else:
                st.info("Nenhuma injetora cadastrada ou encontrada com os filtros")
        except Exception as e:
            st.error(f"Erro ao buscar injetoras: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    with tab3:
        st.subheader("Registro de Manutenção")
        
        # Selecionar injetora
        injetoras = Injetora.get_todos()
        if injetoras:
            with st.form("form_manutencao"):
                injetora_id = st.selectbox(
                    "Selecione a Injetora",
                    options=[i.id for i in injetoras],
                    format_func=lambda x: next(
                        i.numero for i in injetoras if i.id == x
                    )
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    data_manutencao = st.date_input(
                        "Data da Manutenção",
                        value=date.today()
                    )
                    tipo_manutencao = st.selectbox(
                        "Tipo de Manutenção",
                        ["Preventiva", "Corretiva"]
                    )
                    tecnico = st.text_input("Técnico Responsável")
                
                with col2:
                    custo = st.number_input(
                        "Custo (R$)",
                        min_value=0.0,
                        step=0.01
                    )
                    tempo_parado = st.number_input(
                        "Tempo Parado (horas)",
                        min_value=0.0,
                        step=0.5
                    )
                
                descricao = st.text_area("Descrição do Serviço")
                
                submitted = st.form_submit_button(
                    "Registrar Manutenção",
                    use_container_width=True
                )
                
                if submitted:
                    try:
                        injetora = Injetora.get_by_id(injetora_id)
                        if injetora:
                            injetora.registrar_manutencao(
                                data=data_manutencao,
                                tipo_manutencao=tipo_manutencao,
                                descricao=descricao,
                                tecnico=tecnico,
                                custo=custo,
                                tempo_parado=tempo_parado
                            )
                            st.success("✅ Manutenção registrada com sucesso!")
                        else:
                            st.error("Injetora não encontrada")
                    except DatabaseError as e:
                        st.error(f"❌ Erro ao registrar manutenção: {str(e)}")
        else:
            st.info("Nenhuma injetora cadastrada")