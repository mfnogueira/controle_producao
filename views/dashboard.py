import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.connection import execute_query
from utils.formatters import format_decimal

def render_dashboard_view():
    st.title("📊 Dashboard de Produção")
    
    # Filtros de data
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input(
            "Data Inicial",
            value=datetime.now().date() - timedelta(days=30)
        )
    with col2:
        data_final = st.date_input(
            "Data Final",
            value=datetime.now().date()
        )

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    # Total de ordens em produção
    total_em_producao = execute_query("""
        SELECT COUNT(*) as count 
        FROM ordens_producao 
        WHERE status = 'Em Produção'
    """, fetch_one=True)['count']

    # Eficiência média
    eficiencia = execute_query("""
        SELECT 
            AVG(CAST(quantidade_produzida AS FLOAT) / quantidade_total * 100) as eficiencia
        FROM ordens_producao
        WHERE status != 'Pendente'
        AND data_inicio BETWEEN ? AND ?
    """, (data_inicial, data_final), fetch_one=True)['eficiencia'] or 0

    # Total produzido no período
    total_produzido = execute_query("""
        SELECT SUM(quantidade_produzida) as total
        FROM producao_diaria
        WHERE data BETWEEN ? AND ?
    """, (data_inicial, data_final), fetch_one=True)['total'] or 0

    # Total de refugo no período
    total_refugo = execute_query("""
        SELECT SUM(refugo_kg) as total
        FROM producao_diaria
        WHERE data BETWEEN ? AND ?
    """, (data_inicial, data_final), fetch_one=True)['total'] or 0

    with col1:
        st.metric("Ordens em Produção", total_em_producao)
    with col2:
        st.metric("Eficiência Média", f"{eficiencia:.1f}%")
    with col3:
        st.metric("Total Produzido", f"{total_produzido:,} peças")
    with col4:
        st.metric("Total Refugo", f"{format_decimal(total_refugo)} kg")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Produção por Material")
        producao_material = pd.DataFrame(execute_query("""
            SELECT 
                op.material,
                SUM(pd.quantidade_produzida) as total
            FROM ordens_producao op
            JOIN producao_diaria pd ON pd.ordem_id = op.id
            WHERE pd.data BETWEEN ? AND ?
            GROUP BY op.material
        """, (data_inicial, data_final)))
        
        if not producao_material.empty:
            st.bar_chart(producao_material.set_index('material'))
        else:
            st.info("Sem dados de produção no período")

    with col2:
        st.subheader("Status das Ordens")
        status_ordens = pd.DataFrame(execute_query("""
            SELECT 
                status,
                COUNT(*) as quantidade
            FROM ordens_producao
            WHERE data_inicio BETWEEN ? AND ?
            GROUP BY status
        """, (data_inicial, data_final)))
        
        if not status_ordens.empty:
            st.bar_chart(status_ordens.set_index('status'))
        else:
            st.info("Sem ordens no período")

    # Tabelas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ordens em Produção")
        ordens_producao = pd.DataFrame(execute_query("""
            SELECT 
                op.numero_pedido as 'Pedido',
                op.cliente as 'Cliente',
                i.numero as 'Injetora',
                m.nome as 'Molde',
                op.quantidade_total as 'Total',
                op.quantidade_produzida as 'Produzido',
                ROUND(CAST(op.quantidade_produzida AS FLOAT) / 
                      op.quantidade_total * 100, 1) as 'Progresso (%)'
            FROM ordens_producao op
            JOIN injetoras i ON op.injetora_id = i.id
            JOIN moldes m ON op.molde_id = m.id
            WHERE op.status = 'Em Produção'
            ORDER BY op.prioridade, op.data_inicio
        """))
        
        if not ordens_producao.empty:
            st.dataframe(ordens_producao)
        else:
            st.info("Nenhuma ordem em produção")

    with col2:
        st.subheader("Manutenções Pendentes")
        manutencoes = pd.DataFrame(execute_query("""
            SELECT 
                'Injetora' as tipo,
                numero as equipamento,
                manutencao_proxima as data
            FROM injetoras
            WHERE manutencao_proxima <= date('now', '+7 days')
            UNION ALL
            SELECT 
                'Molde' as tipo,
                nome as equipamento,
                CAST(ciclos_desde_manutencao AS TEXT) || '/' || 
                CAST(manutencao_proxima AS TEXT) as data
            FROM moldes
            WHERE ciclos_desde_manutencao >= manutencao_proxima * 0.9
            ORDER BY data
        """))
        
        if not manutencoes.empty:
            st.dataframe(manutencoes)
        else:
            st.success("Nenhuma manutenção pendente")