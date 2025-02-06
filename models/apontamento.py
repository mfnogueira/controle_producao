import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import get_connection, DatabaseError
from utils.formatters import format_decimal, parse_decimal, get_turno_atual
from config.settings import TURNOS

def carregar_ordens_ativas():
    """Carrega ordens ativas do banco de dados."""
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    op.id,
                    op.numero_pedido,
                    op.cliente,
                    i.numero as injetora,
                    m.nome as molde,
                    op.quantidade_total,
                    op.quantidade_produzida,
                    op.material,
                    op.status
                FROM ordens_producao op
                JOIN injetoras i ON op.injetora_id = i.id
                JOIN moldes m ON op.molde_id = m.id
                WHERE op.status IN ('Pendente', 'Em Produção')
                ORDER BY op.data_inicio DESC, op.prioridade
            """
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar ordens: {str(e)}")
        return pd.DataFrame()

def registrar_apontamento(dados):
    """Registra um novo apontamento de produção."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Primeiro verifica se a quantidade não excede o total
            cursor.execute("""
                SELECT quantidade_total, quantidade_produzida
                FROM ordens_producao
                WHERE id = ?
            """, (dados['ordem_id'],))
            
            ordem = cursor.fetchone()
            if not ordem:
                raise ValueError("Ordem não encontrada")
                
            nova_qtd_total = ordem['quantidade_produzida'] + dados['quantidade_produzida']
            if nova_qtd_total > ordem['quantidade_total']:
                raise ValueError(f"Quantidade excede o total do pedido! Máximo permitido: {ordem['quantidade_total'] - ordem['quantidade_produzida']} peças")
            
            # Inserir o apontamento
            cursor.execute("""
                INSERT INTO producao_diaria (
                    ordem_id, data, turno, quantidade_produzida,
                    refugo_kg, operador, observacoes, data_registro
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dados['ordem_id'],
                dados['data'].strftime('%Y-%m-%d'),
                dados['turno'],
                dados['quantidade_produzida'],
                dados['refugo_kg'],
                dados['operador'],
                dados['observacoes'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Atualizar a ordem de produção
            cursor.execute("""
                UPDATE ordens_producao
                SET quantidade_produzida = quantidade_produzida + ?,
                    status = CASE 
                        WHEN quantidade_produzida + ? >= quantidade_total THEN 'Concluído'
                        ELSE 'Em Produção'
                    END
                WHERE id = ?
            """, (
                dados['quantidade_produzida'],
                dados['quantidade_produzida'],
                dados['ordem_id']
            ))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Erro ao registrar apontamento: {str(e)}")
        return False

def render_apontamento_view():
    st.title("📝 Apontamento de Produção")
    
    # Carregar ordens ativas
    ordens_ativas = carregar_ordens_ativas()
    
    if not ordens_ativas.empty:
        with st.form("form_apontamento"):
            # Criar lista formatada de ordens para seleção
            ordem_options = {
                str(row['id']): f"{row['numero_pedido']} - {row['cliente']} ({row['quantidade_produzida']}/{row['quantidade_total']} peças)"
                for _, row in ordens_ativas.iterrows()
            }
            
            ordem_selecionada = st.selectbox(
                "Selecione a Ordem de Produção",
                options=list(ordem_options.keys()),
                format_func=lambda x: ordem_options[x]
            )
            
            if ordem_selecionada:
                ordem = ordens_ativas[ordens_ativas['id'] == int(ordem_selecionada)].iloc[0]
                st.info(f"""
                    📋 Detalhes da Ordem:
                    - Injetora: {ordem['injetora']}
                    - Molde: {ordem['molde']}
                    - Material: {ordem['material']}
                    - Progresso: {(ordem['quantidade_produzida'] / ordem['quantidade_total'] * 100):.1f}%
                """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                data_producao = st.date_input(
                    "Data da Produção",
                    value=datetime.now().date()
                )
                
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
            
            with col2:
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
                
                operador = st.text_input("Operador")
                observacoes = st.text_area("Observações", height=100)
            
            submitted = st.form_submit_button(
                "Registrar Produção",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not operador:
                    st.error("⚠️ Por favor, informe o operador!")
                    return
                
                if qtd_produzida <= 0:
                    st.error("⚠️ A quantidade produzida deve ser maior que zero!")
                    return
                
                if refugo_kg < 0:
                    st.error("⚠️ O refugo não pode ser negativo!")
                    return
                
                dados_apontamento = {
                    'ordem_id': int(ordem_selecionada),
                    'data': data_producao,
                    'turno': turno,
                    'quantidade_produzida': qtd_produzida,
                    'refugo_kg': refugo_kg,
                    'operador': operador,
                    'observacoes': observacoes
                }
                
                if registrar_apontamento(dados_apontamento):
                    st.success("✅ Produção registrada com sucesso!")
                    st.balloons()
                    
                    # Mostrar resumo do apontamento
                    st.info(f"""
                        📊 Resumo do apontamento:
                        - Quantidade produzida: {qtd_produzida} peças
                        - Refugo: {format_decimal(refugo_kg)} kg
                        - Turno: {TURNOS[turno]['descricao']}
                        - Operador: {operador}
                    """)
                    
                    # Recarregar a página
                    st.experimental_rerun()
                
        # Mostrar histórico de apontamentos da ordem selecionada
        if ordem_selecionada:
            st.subheader("Histórico de Apontamentos")
            with get_connection() as conn:
                historico = pd.read_sql_query("""
                    SELECT 
                        data as 'Data',
                        turno as 'Turno',
                        quantidade_produzida as 'Quantidade',
                        refugo_kg as 'Refugo (kg)',
                        operador as 'Operador',
                        observacoes as 'Observações'
                    FROM producao_diaria
                    WHERE ordem_id = ?
                    ORDER BY data DESC, data_registro DESC
                """, conn, params=(ordem_selecionada,))
                
                if not historico.empty:
                    st.dataframe(historico)
                else:
                    st.info("Nenhum apontamento registrado para esta ordem")
                    
    else:
        st.warning("⚠️ Não há ordens de produção ativas no momento.")
        st.info("Para criar uma nova ordem, vá para a seção 'Ordem de Produção'.")