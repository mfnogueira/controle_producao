import streamlit as st
import pandas as pd
from datetime import datetime
from models import apontamento
from utils.formatters import format_decimal, parse_decimal, get_turno_atual
from config.settings import TURNOS
from database.connection import get_connection, DatabaseError

def criar_schema_apontamento():
    """Cria ou atualiza o schema das tabelas de apontamento."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Adicionar coluna de turno se não existir
            cursor.execute("""
                SELECT COUNT(*)
                FROM pragma_table_info('producao_diaria')
                WHERE name='turno'
            """)
            result = cursor.fetchone()
            if result is not None and result[0] == 0:
                cursor.execute("""
                    ALTER TABLE producao_diaria
                    ADD COLUMN turno TEXT DEFAULT 'A'
                """)

            # Renomear coluna refugo para refugo_kg se necessário
            cursor.execute("""
                SELECT COUNT(*)
                FROM pragma_table_info('producao_diaria')
                WHERE name='refugo'
            """)
            result = cursor.fetchone()
            if result is not None and result[0] > 0:
                cursor.execute("""
                    ALTER TABLE producao_diaria
                    RENAME COLUMN refugo TO refugo_kg
                """)

            conn.commit()
    except DatabaseError as e:
        st.error(f"Erro ao criar/atualizar schema: {str(e)}")
    except Exception as e:
        st.error(f"Erro inesperado ao criar/atualizar schema: {str(e)}")

def render_apontamento_view():
    st.title("📝 Apontamento de Produção")

    # Carregar ordens em produção
    try:
        with get_connection() as conn:
            ordens_ativas = pd.read_sql_query("""
                SELECT
                    op.id,
                    op.numero_pedido,
                    op.cliente,
                    i.numero as injetora,
                    m.nome as molde,
                    op.quantidade_total,
                    op.quantidade_produzida
                FROM ordens_producao op
                JOIN injetoras i ON op.injetora_id = i.id
                JOIN moldes m ON op.molde_id = m.id
                WHERE op.status IN ('Em Produção', 'Pendente')
            """, conn)
    except DatabaseError as e:
        st.error(f"Erro ao carregar ordens de produção: {str(e)}")
        return
    except Exception as e:
        st.error(f"Erro inesperado ao carregar ordens de produção: {str(e)}")
        return

    if not ordens_ativas.empty:
        with st.form("form_apontamento"):
            ordem_selecionada = st.selectbox(
                "Selecione a Ordem de Produção",
                options=ordens_ativas['id'],
                format_func=lambda x: f"Pedido: {ordens_ativas[ordens_ativas['id']==x]['numero_pedido'].iloc[0]} - Cliente: {ordens_ativas[ordens_ativas['id']==x]['cliente'].iloc[0]}"
            )

            col1, col2 = st.columns(2)

            with col1:
                data_producao = st.date_input("Data da Produção")
                turno = st.selectbox(
                    "Turno",
                    options=list(TURNOS.keys()),
                    format_func=lambda x: TURNOS[x]['descricao'],
                    index=list(TURNOS.keys()).index(get_turno_atual())
                )

                # Campo de quantidade com validação numérica
                qtd_str = st.text_input(
                    "Quantidade Produzida",
                    value="0",
                    help="Use ponto ou vírgula como separador decimal"
                )
                try:
                    qtd_produzida = int(parse_decimal(qtd_str))
                except ValueError:
                    st.error("Quantidade inválida")
                    qtd_produzida = 0

                # Campo de refugo em kg com validação
                refugo_str = st.text_input(
                    "Refugo (kg)",
                    value="0,0",
                    help="Use ponto ou vírgula como separador decimal"
                )
                try:
                    refugo_kg = parse_decimal(refugo_str)
                except ValueError:
                    st.error("Valor de refugo inválido")
                    refugo_kg = 0.0

            with col2:
                operador = st.text_input("Operador")
                observacoes = st.text_area("Observações", height=100)

            submitted = st.form_submit_button(
                "Registrar Produção",
                use_container_width=True
            )

            if submitted:
                try:
                    if qtd_produzida <= 0:
                        st.error("A quantidade produzida deve ser maior que zero")
                        return

                    if refugo_kg < 0:
                        st.error("O refugo não pode ser negativo")
                        return

                    if not operador:
                        st.error("Informe o operador")
                        return

                    # Criar e salvar apontamento
                    apontamento = Apontamento.criar(
                        ordem_id=ordem_selecionada,
                        quantidade_produzida=qtd_produzida,
                        refugo_kg=refugo_kg,
                        operador=operador,
                        observacoes=observacoes,
                        data=data_producao,
                        turno=turno
                    )

                    apontamento.salvar()
                    st.success("✅ Produção registrada com sucesso!")

                    # Mostrar resumo do apontamento
                    st.info(f"""
                        📊 Resumo do apontamento:
                        - Quantidade: {qtd_produzida} peças
                        - Refugo: {format_decimal(refugo_kg)} kg
                        - Turno: {TURNOS[turno]['descricao']}
                        - Operador: {operador}
                    """)

                except Exception as e:
                    st.error(f"❌ Erro ao registrar produção: {str(e)}")
    else:
        st.info("Não há ordens de produção ativas no momento.")
