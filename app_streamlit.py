import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(page_title="DFImóveis Dashboard", page_icon="🏠", layout="wide")
st.title("🏠 DFImóveis — Plano Piloto, DF")
st.markdown("---")


# ── Resumo ──────────────────────────────────────────────────
st.subheader("📊 Resumo Geral")
try:
    resumo = requests.get(f"{API_URL}/imoveis-resumo", timeout=5).json()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Imóveis", resumo["total_imoveis"])
    col2.metric("Preço Médio Aluguel", f"R$ {resumo['preco_medio_aluguel']:,.2f}" if resumo["preco_medio_aluguel"] else "—")
    col3.metric("Preço Médio Venda", f"R$ {resumo['preco_medio_venda']:,.2f}" if resumo["preco_medio_venda"] else "—")
    col4.metric("Apartamentos / Casas", f"{resumo['total_apartamentos']} / {resumo['total_casas']}")

except Exception as e:
    st.error(f"Não foi possível conectar na API: {e}")
    st.stop()

st.markdown("---")

# ── Tabela de Imóveis ────────────────────────────────────────
st.subheader("📋 Imóveis Cadastrados")

imoveis_raw = requests.get(f"{API_URL}/imoveis", timeout=5).json()

if not imoveis_raw:
    st.info("Nenhum imóvel cadastrado ainda. Use o Postman para inserir via POST /imoveis")
else:
    df = pd.DataFrame([
        {
            "ID": i["id"],
            "Endereço": i["endereco"],
            "Tipo": i["tipo_imovel"]["nome_tipo_imovel"],
            "Operação": i["tipo_operacao"]["nome_operacao"],
            "Preço (R$)": i["preco"],
            "Tamanho (m²)": i["tamanho_m2"],
            "Quartos": i["quartos"],
            "Vagas": i["vagas"],
            "Suítes": i["suites"],
            "Imobiliária": i["imobiliaria"]["nome_imobiliaria"] if i["imobiliaria"] else "—",
            "Data Coleta": i["data_coleta"],
        }
        for i in imoveis_raw
    ])

    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_op = st.selectbox("Filtrar por Operação", ["Todos", "ALUGUEL", "VENDA"])
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "APARTAMENTO", "CASA"])

    df_filtrado = df.copy()
    if filtro_op != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Operação"] == filtro_op]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]

    st.dataframe(df_filtrado, use_container_width=True)

    st.markdown("---")

    # ── Gráficos ─────────────────────────────────────────────
    st.subheader("📈 Gráficos")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig_op = px.pie(
            df, names="Operação", title="Distribuição por Operação",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_op, use_container_width=True)

    with col_g2:
        fig_tipo = px.pie(
            df, names="Tipo", title="Distribuição por Tipo de Imóvel",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_tipo, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        fig_preco = px.box(
            df, x="Operação", y="Preço (R$)", color="Tipo",
            title="Distribuição de Preços por Operação e Tipo",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_preco, use_container_width=True)

    with col_g4:
        if df["Tamanho (m²)"].notna().any():
            fig_m2 = px.scatter(
                df, x="Tamanho (m²)", y="Preço (R$)", color="Tipo",
                hover_data=["Endereço", "Operação"],
                title="Preço x Tamanho (m²)",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_m2, use_container_width=True)
        else:
            st.info("Sem dados de tamanho para exibir gráfico de dispersão.")
