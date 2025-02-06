import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from models.ordem_producao import OrdemProducao
from models.injetora import Injetora
from models.molde import Molde
from utils.formatters import format_decimal
from database.connection import DatabaseError, get_table_download_link
from config.settings import MATERIAIS

def gerar_numero_pedido() -> str:
    """Gera número de pedido no formato PED-YYYYMMDD-XXX."""
    hoje = datetime.now()
    # Buscar último pedido do dia
    try:
        ultimos_pedidos = [op.numero_pedido for op in OrdemProducao.get_por_periodo(hoje.date(), hoje.date())]
        
        if not ultimos_pedidos:
            seq = 1
        else:
            # Extrair última sequência
            seq = max([
                int(num.split('-')[2])
                for num in ultimos_pedidos
                if num.startswith(f"PED-{hoje.strftime('%Y%m%d')}")
            ] + [0]) + 1
        
        return f"PED-{hoje.strftime('%Y%m%d')}-{str(seq).zfill(3)}"
    except Exception as e:
        st.error(f"Erro ao gerar número do pedido: {str(e)}")
        return f"PED-{hoje.strftime('%Y%m%d')}-001"

def render_ordens_view():
    st.title("📋 Ordens de Produção")
    
    tab1, tab2, tab3 = st.tabs(["Nova Ordem", "Visualização", "Encerramento"])
    
    with tab1:
        with st.form("form_ordem"):
            st.subheader("Nova Ordem de Produção")
            
            # Número do pedido automático
            numero_pedido = gerar_numero_pedido()
            st.info(f"Número do Pedido: {numero_pedido}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                cliente = st.text_input("Cliente")
                
                # Carregar injetoras disponíveis
                injetoras = Injetora.get_disponiveis()
                if injetoras:
                    injetora_selecionada = st.selectbox(
                        "Selecione a Injetora",
                        options=[i.id for i in injetoras],
                        format_func=lambda x: next(
                            f"{i.numero} ({i.capacidade_ton}ton)"
                            for i in injetoras if i.id == x
                        )
                    )
                else:
                    st.error("❌ Nenhuma injetora disponível!")
                    injetora_selecionada = None
                
                # Carregar moldes disponíveis
                moldes = Molde.get_disponiveis()
                if moldes:
                    molde_selecionado = st.selectbox(
                        "Selecione o Molde",
                        options=[m.id for m in moldes],
                        format_func=lambda x: next(
                            f"{m.nome} ({m.num_cavidades} cavidades)"
                            for m in moldes if m.id == x
                        )
                    )
                else:
                    st.error("❌ Nenhum molde disponível!")
                    molde_selecionado = None
                
                material = st.selectbox("Material", MATERIAIS)
                
            with col2:
                quantidade = st.number_input(
                    "Quantidade Total",
                    min_value=1,
                    help="Quantidade total de peças a produzir"
                )
                ciclo = st.number_input(
                    "Ciclo (segundos)",
                    min_value=0.1,
                    value=30.0,
                    step=0.1,
                    help="Tempo de ciclo em segundos"
                )
                master = st.number_input(
                    "Percentual de Master (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=3.0,
                    step=0.1
                )
                peso_peca = st.number_input(
                    "Peso da Peça (g)",
                    min_value=0.0,
                    step=0.1,
                    help="Peso da peça em gramas"
                )
            
            col3, col4 = st.columns(2)
            with col3:
                data_inicio = st.date_input(
                    "Data de Início",
                    min_value=date.today()
                )
                prioridade = st.selectbox(
                    "Prioridade",
                    options=[1, 2, 3],
                    format_func=lambda x: {
                        1: "Alta",
                        2: "Média",
                        3: "Baixa"
                    }[x]
                )
            
            observacoes = st.text_area("Observações")
            
            submitted = st.form_submit_button(
                "Gerar Ordem de Produção",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not all([cliente, injetora_selecionada, molde_selecionado]):
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    try:
                        st.info("Criando ordem de produção...")
                        ordem = OrdemProducao.criar(
                            numero_pedido=numero_pedido,
                            cliente=cliente,
                            injetora_id=injetora_selecionada,
                            molde_id=molde_selecionado,
                            quantidade_total=quantidade,
                            ciclo_segundos=ciclo,
                            material=material,
                            percentual_master=master,
                            peso_peca=peso_peca,
                            data_inicio=data_inicio,
                            prioridade=prioridade,
                            observacoes=observacoes
                        )
                        ordem.salvar()
                        st.success("✅ Ordem de produção gerada com sucesso!")
                        st.info(f"ID da ordem: {ordem.id}")
                        
                        # Mostrar resumo
                        st.info(f"""
                            📊 Resumo da Ordem:
                            - Pedido: {numero_pedido}
                            - Cliente: {cliente}
                            - Quantidade: {quantidade:,} peças
                            - Material: {material} + {master}% master
                            - Peso Total Estimado: {format_decimal(ordem.peso_total)} kg
                        """)
                    except (ValueError, DatabaseError) as e:
                        st.error(f"❌ Erro ao gerar ordem: {str(e)}")
    
    with tab2:
        st.subheader("Ordens de Produção")
        
        try:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_status = st.selectbox(
                    "Status",
                    ["Todos", "Pendente", "Em Produção", "Concluído", "Atrasado"]
                )
            with col2:
                filtro_material = st.selectbox(
                    "Material",
                    ["Todos"] + MATERIAIS
                )
            with col3:
                filtro_periodo = st.selectbox(
                    "Período",
                    ["Hoje", "Última Semana", "Último Mês", "Todos"]
                )
            
            # Calcular datas para filtro
            hoje = date.today()
            if filtro_periodo == "Hoje":
                data_inicial = hoje
                data_final = hoje
            elif filtro_periodo == "Última Semana":
                data_inicial = hoje - timedelta(days=7)
                data_final = hoje
            elif filtro_periodo == "Último Mês":
                data_inicial = hoje - timedelta(days=30)
                data_final = hoje
            else:
                data_inicial = date(2000, 1, 1)
                data_final = date(2100, 12, 31)
            
            st.info("Buscando ordens de produção...")
            ordens = OrdemProducao.get_por_periodo(data_inicial, data_final)
            st.info(f"Total de ordens encontradas: {len(ordens)}")
            
            # Debug: mostrar dados brutos
            if st.checkbox("Mostrar dados brutos"):
                for o in ordens:
                    st.write(o)
            
            # Aplicar filtros
            if filtro_status != "Todos":
                ordens = [o for o in ordens if o.status == filtro_status]
            if filtro_material != "Todos":
                ordens = [o for o in ordens if o.material == filtro_material]
            
            if ordens:
                # Converter para DataFrame
                df = pd.DataFrame([{
                    'Pedido': o.numero_pedido,
                    'Cliente': o.cliente,
                    'Material': o.material,
                    'Quantidade Total': o.quantidade_total,
                    'Produzido': o.quantidade_produzida,
                    'Progresso (%)': round(o.get_eficiencia(), 1),
                    'Data Início': o.data_inicio,
                    'Data Fim': o.data_fim,
                    'Status': o.status
                } for o in ordens])
                
                # Mostrar tabela
                st.dataframe(df)
                
                # Botão de download
                st.markdown(
                    get_table_download_link(df, "ordens_producao"),
                    unsafe_allow_html=True
                )
            else:
                st.info("Nenhuma ordem encontrada com os filtros selecionados")
        except Exception as e:
            st.error(f"Erro ao buscar ordens: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    with tab3:
        st.subheader("Encerramento de Ordem")
        
        try:
            # Buscar apenas ordens em produção
            ordens_ativas = [o for o in OrdemProducao.get_em_producao()
                           if o.status in ['Em Produção', 'Atrasado']]
            
            if ordens_ativas:
                with st.form("form_encerramento"):
                    ordem_id = st.selectbox(
                        "Selecione a Ordem",
                        options=[o.id for o in ordens_ativas],
                        format_func=lambda x: next(
                            f"{o.numero_pedido} - {o.cliente} ({o.quantidade_produzida}/{o.quantidade_total})"
                            for o in ordens_ativas if o.id == x
                        )
                    )
                    
                    motivo = st.text_area("Motivo do Encerramento")
                    
                    submitted = st.form_submit_button(
                        "Encerrar Ordem",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    if submitted:
                        try:
                            ordem = OrdemProducao.get_by_id(ordem_id)
                            if ordem:
                                ordem.cancelar(motivo)
                                st.success("✅ Ordem encerrada com sucesso!")
                            else:
                                st.error("Ordem não encontrada")
                        except DatabaseError as e:
                            st.error(f"❌ Erro ao encerrar ordem: {str(e)}")
            else:
                st.info("Nenhuma ordem em produção para encerrar")
        except Exception as e:
            st.error(f"Erro ao buscar ordens ativas: {str(e)}")
            import traceback
            st.code(traceback.format_exc())