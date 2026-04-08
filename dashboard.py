import altair as alt
import pandas as pd
import streamlit as st

from services.box_office import DataFetchError, get_box_office_data


def render_dashboard() -> None:
    st.set_page_config(layout="wide")
    render_header()
    render_sidebar()

    try:
        df = get_box_office_data()
    except DataFetchError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.warning("Nenhum dado foi encontrado para exibição no momento.")
        return

    num_filmes, worldwide_range = render_filters(df)
    df_filtrado = df[
        (df["Mundialmente"] >= worldwide_range[0])
        & (df["Mundialmente"] <= worldwide_range[1])
    ]
    df_filtrado_top_n = df_filtrado.nlargest(num_filmes, "Mundialmente")

    render_metrics(df_filtrado)
    render_tabs(df_filtrado_top_n, num_filmes)


def render_header() -> None:
    col_logo, col_titulo = st.columns([0.05, 0.95], gap="small")
    with col_logo:
        st.image(
            "https://emojipedia-us.s3.amazonaws.com/source/skype/289/clapper-board_1f3ac.png",
            width=80,
        )
    with col_titulo:
        st.title("Bilhetrometro")
        st.markdown("Visualize a bilheteira mundial dos principais filmes.")
    st.divider()


def render_sidebar() -> None:
    st.sidebar.header("Ações")
    if st.sidebar.button("Atualizar bilheteria mundial"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.divider()
    st.sidebar.header("Filtros do Dashboard")
    with st.sidebar.expander("Sobre o projeto"):
        st.write(
            """
            Fonte dos dados: Box Office Mojo.
            Desenvolvido por: José Yure

            Este dashboard interativo foi construído com Streamlit para analisar
            a bilheteria mundial de filmes.
            """
        )


def render_filters(df: pd.DataFrame) -> tuple[int, tuple[int, int]]:
    num_filmes = st.sidebar.slider(
        "Selecione o número de filmes:",
        min_value=5,
        max_value=len(df),
        value=min(10, len(df)),
        step=1,
    )
    max_worldwide_value = df["Mundialmente"].max()
    max_worldwide = (
        1_000_000_000 if pd.isna(max_worldwide_value) else int(max_worldwide_value)
    )
    if max_worldwide <= 0:
        max_worldwide = 1_000_000_000
    worldwide_range = st.sidebar.slider(
        "Filtrar por valor de bilheteira:",
        min_value=0,
        max_value=max_worldwide,
        value=(0, max_worldwide),
    )
    return num_filmes, worldwide_range


def render_metrics(df_filtrado: pd.DataFrame) -> None:
    st.header("Métricas Principais")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Bilheteira Mundial Total",
            value=f"${df_filtrado['Mundialmente'].sum():,.0f}",
        )
    with col2:
        if not df_filtrado.empty and not df_filtrado["Mundialmente"].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado["Mundialmente"].idxmax()]
            st.metric(
                label=f"Maior Bilheteira Mundial ({top_movie['Título']})",
                value=f"${top_movie['Mundialmente']:,.0f}",
            )
    with col3:
        if not df_filtrado.empty and not df_filtrado["EUA/Canadá"].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado["EUA/Canadá"].idxmax()]
            st.metric(
                label=f"Maior Bilheteira Doméstica ({top_movie['Título']})",
                value=f"${top_movie['EUA/Canadá']:,.0f}",
            )
    with col4:
        if not df_filtrado.empty and not df_filtrado["EUA/Canadá (%)"].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado["EUA/Canadá (%)"].idxmax()]
            st.metric(
                label=f"Maior % Bilheteira EUA/Canadá ({top_movie['Título']})",
                value=f"{top_movie['EUA/Canadá (%)'] * 100:.2f}%",
            )


def render_tabs(df_filtrado_top_n: pd.DataFrame, num_filmes: int) -> None:
    st.header("Análise Visual dos Filmes")
    tab1, tab2 = st.tabs(["Gráfico de Barras", "Tabela Detalhada"])

    with tab1:
        st.subheader(f"Top {num_filmes} Filmes por Bilheteira Mundial")
        if df_filtrado_top_n.empty:
            st.warning("Nenhum filme encontrado com os filtros aplicados.")
            return
        chart = (
            alt.Chart(df_filtrado_top_n)
            .mark_bar()
            .encode(
                x=alt.X("Mundialmente", title="Bilheteira Mundial ($)"),
                y=alt.Y("Título", sort="-x", title="Filme"),
                tooltip=[
                    "Título",
                    alt.Tooltip("Mundialmente", format="$,.0f"),
                    alt.Tooltip("EUA/Canadá", format="$,.0f"),
                ],
            )
            .properties(title=f"Top {num_filmes} Filmes por Bilheteira Mundial")
        )
        st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.subheader("Dados dos Filmes Selecionados")
        df_display = df_filtrado_top_n[
            ["Rank", "Título", "Mundialmente", "EUA/Canadá", "EUA/Canadá (%)"]
        ]
        df_styled = df_display.style.format(
            {
                "Mundialmente": "${:,.0f}",
                "EUA/Canadá": "${:,.0f}",
                "EUA/Canadá (%)": "{:.2%}",
            }
        ).background_gradient(cmap="viridis", subset=["Mundialmente", "EUA/Canadá"])
        st.dataframe(df_styled, hide_index=True, use_container_width=True)
