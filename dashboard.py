from __future__ import annotations

from dataclasses import dataclass

import altair as alt
import pandas as pd
import streamlit as st

# Fazemos o mock do import para evitar erros caso o serviço não esteja no mesmo diretório
try:
    from services.box_office import DataFetchError, get_box_office_data
except ImportError:
    class DataFetchError(Exception):
        pass
    def get_box_office_data():
        # Fallback de dados dummy para testes visuais
        return pd.DataFrame({
            "Rank": [1, 2, 3],
            "Titulo": ["Avatar", "Vingadores: Ultimato", "Avatar: O Caminho da Água"],
            "Mundialmente": [2923706026, 2799439100, 2320250281],
            "EUA/Canada": [785220696, 858373000, 684075767],
            "EUA/Canada (%)": [0.268, 0.306, 0.294]
        })

TITLE = "Titulo"
WORLDWIDE = "Worldwide"
DOMESTIC = "Domestic"
DOMESTIC_SHARE = "DomesticShare"
INTERNATIONAL = "International"
INTERNATIONAL_SHARE = "InternationalShare"

SORT_OPTIONS = {
    "Bilheteria mundial": WORLDWIDE,
    "Bilheteria domestica": DOMESTIC,
    "Bilheteria internacional": INTERNATIONAL,
    "Participacao domestica": DOMESTIC_SHARE,
    "Participacao internacional": INTERNATIONAL_SHARE,
}


@dataclass(frozen=True)
class DashboardFilters:
    search: str
    top_n: int
    worldwide_range: tuple[int, int]
    domestic_share_range: tuple[int, int]
    include_unknown_domestic_share: bool
    sort_label: str


def render_dashboard() -> None:
    st.set_page_config(
        page_title="Bilhetrometro Dashboard",
        page_icon=":movie_camera:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    try:
        df = prepare_data(get_box_office_data())
    except DataFetchError as exc:
        render_header(pd.DataFrame(), pd.DataFrame())
        st.error(str(exc))
        return

    if df.empty:
        render_header(df, df)
        st.warning("Nenhum dado foi encontrado para exibicao no momento.")
        return

    filters = render_sidebar(df)
    filtered_df = apply_filters(df, filters)
    sort_column = SORT_OPTIONS[filters.sort_label]
    top_df = get_top_movies(filtered_df, sort_column, filters.top_n)

    render_header(filtered_df, df)

    if filtered_df.empty:
        st.warning("Nenhum filme encontrado com os filtros aplicados.")
        return

    render_metrics(filtered_df, df)
    
    # Adicionando uma quebra para o layout
    st.markdown("<br>", unsafe_allow_html=True)
    
    render_spotlight(filtered_df)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    render_tabs(filtered_df, top_df, sort_column, filters)


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Titulo": TITLE,
        "Mundialmente": WORLDWIDE,
        "EUA/Canada": DOMESTIC,
        "EUA/Canada (%)": DOMESTIC_SHARE,
    }
    prepared = df.rename(columns=rename_map).copy()

    numeric_columns = [WORLDWIDE, DOMESTIC, DOMESTIC_SHARE]
    for column in numeric_columns:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    prepared[DOMESTIC] = prepared[DOMESTIC].clip(lower=0)
    prepared[INTERNATIONAL] = (prepared[WORLDWIDE] - prepared[DOMESTIC]).clip(lower=0)
    prepared[INTERNATIONAL_SHARE] = prepared[INTERNATIONAL] / prepared[WORLDWIDE]
    prepared[INTERNATIONAL_SHARE] = prepared[INTERNATIONAL_SHARE].replace(
        [float("inf"), -float("inf")], pd.NA
    )
    if "Rank" in prepared.columns:
        prepared["Rank"] = pd.to_numeric(prepared["Rank"], errors="coerce")
    prepared[TITLE] = prepared[TITLE].fillna("Sem titulo")
    return prepared.sort_values(WORLDWIDE, ascending=False)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        /* Estilos Modernos - Dark / Glassmorphism Vibe Misto com Corporativo */
        :root {
            --bilhete-bg: #0e1117;
            --bilhete-surface: #1e212b;
            --bilhete-border: #333845;
            --bilhete-ink: #ffffff;
            --bilhete-muted: #a3a8b8;
            --bilhete-primary: #0ea5e9;
            --bilhete-accent: #f43f5e;
            --bilhete-gradient: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 50%, #8b5cf6 100%);
        }

        .stApp {
            background-color: var(--bilhete-bg);
            color: var(--bilhete-ink);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* Estilos dos Métricas */
        [data-testid="stMetric"] {
            background: var(--bilhete-surface);
            border: 1px solid var(--bilhete-border);
            border-radius: 12px;
            padding: 1.25rem;
            min-height: 120px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
            border-color: var(--bilhete-primary);
        }

        [data-testid="stMetricLabel"] p {
            color: var(--bilhete-muted);
            font-size: 0.95rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--bilhete-ink);
            font-size: clamp(1.5rem, 2.5vw, 2.2rem);
            font-weight: 800;
        }

        /* Hero Section com Gradiente Vibrante */
        .hero {
            background: var(--bilhete-gradient);
            color: white;
            border-radius: 16px;
            padding: clamp(1.5rem, 4vw, 3rem);
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(14, 165, 233, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .hero::after {
            content: '';
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            background: url('https://www.transparenttextures.com/patterns/carbon-fibre.png');
            opacity: 0.1;
            pointer-events: none;
        }

        .hero h1 {
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 900;
            line-height: 1.1;
            margin: 0 0 1rem;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .hero p {
            margin: 0;
            color: rgba(255, 255, 255, 0.9);
            max-width: 800px;
            font-size: clamp(1.1rem, 2vw, 1.25rem);
            line-height: 1.6;
        }

        /* Cards de Destaque */
        .spotlight {
            background: var(--bilhete-surface);
            border: 1px solid var(--bilhete-border);
            border-left: 4px solid var(--bilhete-primary);
            border-radius: 12px;
            padding: 1.5rem;
            height: 100%;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .spotlight strong {
            color: var(--bilhete-ink);
            display: block;
            font-size: 1.25rem;
            font-weight: 700;
            line-height: 1.4;
            margin: 0.5rem 0;
        }

        .spotlight span {
            color: var(--bilhete-muted);
            display: block;
            font-size: 0.95rem;
        }
        
        .spotlight span:first-child {
            color: var(--bilhete-primary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }

        @media (max-width: 760px) {
            .block-container {
                padding: 1rem;
            }
            [data-testid="stMetric"] {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> None:
    visible_movies = len(filtered_df)
    total_movies = len(full_df)
    total_worldwide = filtered_df[WORLDWIDE].sum() if not filtered_df.empty else 0

    st.markdown(
        f"""
        <section class="hero">
            <h1>Bilhetrometro</h1>
            <p>
                Um painel interativo para explorar arrecadação mundial, peso doméstico
                e desempenho internacional dos principais filmes.
                <br><br>
                Analisando <strong>{visible_movies}</strong> de
                <strong>{total_movies}</strong> filmes filtrados, somando
                <strong>{format_money(total_worldwide)}</strong>.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(df: pd.DataFrame) -> DashboardFilters:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3163/3163508.png", width=60)
    st.sidebar.markdown("### Controles do Painel")
    
    if st.sidebar.button("Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    
    search = st.sidebar.text_input("Buscar filme", placeholder="Digite parte do titulo")

    max_top_n = max(1, min(50, len(df)))
    top_n = st.sidebar.slider(
        "Quantidade no ranking",
        min_value=1,
        max_value=max_top_n,
        value=min(10, max_top_n),
        step=1,
    )

    max_worldwide = safe_int(df[WORLDWIDE].max(), fallback=1_000_000_000)
    worldwide_range = st.sidebar.slider(
        "Faixa de bilheteria mundial",
        min_value=0,
        max_value=max_worldwide,
        value=(0, max_worldwide),
        step=max(1, max_worldwide // 100),
        format="$%d",
    )

    domestic_share_range = st.sidebar.slider(
        "Participacao EUA/Canada",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=1,
        format="%d%%",
    )
    include_unknown = st.sidebar.checkbox(
        "Incluir filmes sem percentual domestico",
        value=True,
    )

    sort_label = st.sidebar.selectbox(
        "Ordenar ranking por",
        options=list(SORT_OPTIONS.keys()),
        index=0,
    )

    with st.sidebar.expander("Sobre o projeto"):
        st.write(
            """
            Fonte dos dados: Box Office Mojo.
            Desenvolvido por: Jose Yure.

            Use os filtros para comparar desempenho mundial, domestico e
            internacional dos filmes listados.
            """
        )

    return DashboardFilters(
        search=search,
        top_n=top_n,
        worldwide_range=worldwide_range,
        domestic_share_range=domestic_share_range,
        include_unknown_domestic_share=include_unknown,
        sort_label=sort_label,
    )


def apply_filters(df: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    filtered = df[
        df[WORLDWIDE].between(
            filters.worldwide_range[0],
            filters.worldwide_range[1],
            inclusive="both",
        )
    ].copy()

    if filters.search.strip():
        query = filters.search.strip()
        filtered = filtered[
            filtered[TITLE].str.contains(query, case=False, na=False, regex=False)
        ]

    min_share, max_share = [value / 100 for value in filters.domestic_share_range]
    has_share_in_range = filtered[DOMESTIC_SHARE].between(
        min_share,
        max_share,
        inclusive="both",
    )
    if filters.include_unknown_domestic_share:
        filtered = filtered[has_share_in_range | filtered[DOMESTIC_SHARE].isna()]
    else:
        filtered = filtered[has_share_in_range]

    return filtered


def get_top_movies(df: pd.DataFrame, sort_column: str, top_n: int) -> pd.DataFrame:
    if df.empty:
        return df
    return (
        df.sort_values(sort_column, ascending=False, na_position="last")
        .head(top_n)
        .copy()
    )


def render_metrics(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> None:
    selected_total = filtered_df[WORLDWIDE].sum()
    full_total = full_df[WORLDWIDE].sum()
    selected_share = selected_total / full_total if full_total else 0
    top_movie = get_top_row(filtered_df, WORLDWIDE)
    avg_worldwide = filtered_df[WORLDWIDE].mean()
    domestic_share = filtered_df[DOMESTIC].sum() / selected_total if selected_total else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Bilheteria filtrada",
        format_money(selected_total),
        delta=f"{selected_share:.1%} do total",
    )
    col2.metric("Media por filme", format_money(avg_worldwide))
    col3.metric("Maior bilheteria", format_money(top_movie[WORLDWIDE]), top_movie[TITLE])
    col4.metric("Peso EUA/Canada", format_percent(domestic_share))


def render_spotlight(filtered_df: pd.DataFrame) -> None:
    top_worldwide = get_top_row(filtered_df, WORLDWIDE)
    top_domestic = get_top_row(filtered_df, DOMESTIC)
    top_international = get_top_row(filtered_df, INTERNATIONAL_SHARE)

    st.markdown("### Destaques Principais")
    col1, col2, col3 = st.columns(3)
    with col1:
        spotlight_card(
            "🏆 Campeao mundial",
            top_worldwide[TITLE],
            f"{format_money(top_worldwide[WORLDWIDE])} no total global",
        )
    with col2:
        spotlight_card(
            "🇺🇸 Maior forca domestica",
            top_domestic[TITLE],
            f"{format_money(top_domestic[DOMESTIC])} nos EUA/Canada",
        )
    with col3:
        spotlight_card(
            "🌍 Mais internacional",
            top_international[TITLE],
            f"{format_percent(top_international[INTERNATIONAL_SHARE])} fora dos EUA/Canada",
        )


def spotlight_card(label: str, title: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="spotlight">
            <span>{label}</span>
            <strong>{title}</strong>
            <span>{detail}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tabs(
    filtered_df: pd.DataFrame,
    top_df: pd.DataFrame,
    sort_column: str,
    filters: DashboardFilters,
) -> None:
    st.markdown("### Análise Visual Avançada")
    tab_ranking, tab_mix, tab_scatter, tab_table = st.tabs(
        ["📊 Ranking", "🥧 Composição", "📈 Dispersão", "🗄️ Tabela"]
    )

    with tab_ranking:
        render_ranking_chart(top_df, sort_column, filters.top_n)

    with tab_mix:
        render_composition_chart(top_df, filters.top_n)

    with tab_scatter:
        render_scatter_chart(filtered_df)

    with tab_table:
        render_table(filtered_df, filters)


def render_ranking_chart(top_df: pd.DataFrame, sort_column: str, top_n: int) -> None:
    if top_df.empty:
        st.info("Sem dados para montar o ranking.")
        return

    chart = (
        alt.Chart(top_df)
        .mark_bar(cornerRadiusEnd=6, color="#0ea5e9")
        .encode(
            x=alt.X(f"{sort_column}:Q", title=format_column_label(sort_column)),
            y=alt.Y(f"{TITLE}:N", sort="-x", title=None),
            color=alt.Color(
                f"{INTERNATIONAL_SHARE}:Q",
                scale=alt.Scale(scheme="purples"),
                legend=alt.Legend(title="Peso internacional"),
            ),
            tooltip=movie_tooltips(),
        )
        .properties(height=max(350, top_n * 40))
    )
    st.altair_chart(chart, use_container_width=True)


def render_composition_chart(top_df: pd.DataFrame, top_n: int) -> None:
    if top_df.empty:
        st.info("Sem dados para comparar composicao.")
        return

    chart_data = top_df[[TITLE, DOMESTIC, INTERNATIONAL]].melt(
        id_vars=TITLE,
        value_vars=[DOMESTIC, INTERNATIONAL],
        var_name="Mercado",
        value_name="Bilheteria",
    )
    chart_data["Mercado"] = chart_data["Mercado"].replace(
        {DOMESTIC: "EUA/Canada", INTERNATIONAL: "Internacional"}
    )

    chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Bilheteria:Q", stack="normalize", title="Participacao"),
            y=alt.Y(f"{TITLE}:N", sort=list(top_df[TITLE]), title=None),
            color=alt.Color(
                "Mercado:N",
                scale=alt.Scale(range=["#f43f5e", "#0ea5e9"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip(f"{TITLE}:N", title="Filme"),
                alt.Tooltip("Mercado:N"),
                alt.Tooltip("Bilheteria:Q", title="Bilheteria", format="$,.0f"),
            ],
        )
        .properties(height=max(350, top_n * 40))
    )
    st.altair_chart(chart, use_container_width=True)


def render_scatter_chart(filtered_df: pd.DataFrame) -> None:
    chart_df = filtered_df.dropna(subset=[DOMESTIC, INTERNATIONAL, WORLDWIDE])
    if chart_df.empty:
        st.info("Sem dados suficientes para o grafico de dispersao.")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_circle(opacity=0.8)
        .encode(
            x=alt.X(f"{DOMESTIC}:Q", title="EUA/Canada", axis=alt.Axis(format="$~s")),
            y=alt.Y(
                f"{INTERNATIONAL}:Q",
                title="Internacional",
                axis=alt.Axis(format="$~s"),
            ),
            size=alt.Size(f"{WORLDWIDE}:Q", title="Mundialmente", legend=None, scale=alt.Scale(range=[100, 1000])),
            color=alt.Color(
                f"{DOMESTIC_SHARE}:Q",
                scale=alt.Scale(scheme="plasma"),
                legend=alt.Legend(title="Peso domestico"),
            ),
            tooltip=movie_tooltips(),
        )
        .interactive()
        .properties(height=500)
    )
    st.altair_chart(chart, use_container_width=True)


def render_table(filtered_df: pd.DataFrame, filters: DashboardFilters) -> None:
    if filtered_df.empty:
        st.info("Sem dados para exibir na tabela.")
        return
        
    table_df = filtered_df.sort_values(
        SORT_OPTIONS[filters.sort_label],
        ascending=False,
        na_position="last",
    )
    
    cols = []
    if "Rank" in table_df.columns:
        cols.append("Rank")
    cols.extend([TITLE, WORLDWIDE, DOMESTIC, DOMESTIC_SHARE, INTERNATIONAL, INTERNATIONAL_SHARE])
    
    table_df = table_df[cols]
    
    display_df = table_df.rename(columns=display_column_labels())
    
    format_dict = {
        "Mundialmente": "${:,.0f}",
        "EUA/Canada": "${:,.0f}",
        "EUA/Canada (%)": "{:.1%}",
        "Internacional": "${:,.0f}",
        "Internacional (%)": "{:.1%}",
    }
    if "Rank" in display_df.columns:
        format_dict["Rank"] = "{:.0f}"

    st.dataframe(
        display_df.style.format(
            format_dict,
            na_rep="-",
        ).background_gradient(
            cmap="Blues",
            subset=["Mundialmente", "EUA/Canada", "Internacional"],
        ),
        hide_index=True,
        use_container_width=True,
    )

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name="bilhetrometro_filtrado.csv",
        mime="text/csv",
        use_container_width=True,
    )


def movie_tooltips() -> list[alt.Tooltip]:
    return [
        alt.Tooltip(f"{TITLE}:N", title="Filme"),
        alt.Tooltip(f"{WORLDWIDE}:Q", title="Mundialmente", format="$,.0f"),
        alt.Tooltip(f"{DOMESTIC}:Q", title="EUA/Canada", format="$,.0f"),
        alt.Tooltip(f"{INTERNATIONAL}:Q", title="Internacional", format="$,.0f"),
        alt.Tooltip(f"{DOMESTIC_SHARE}:Q", title="Peso domestico", format=".1%"),
    ]


def format_column_label(column: str) -> str:
    labels = {
        WORLDWIDE: "Bilheteria mundial",
        DOMESTIC: "Bilheteria EUA/Canada",
        INTERNATIONAL: "Bilheteria internacional",
        DOMESTIC_SHARE: "Participacao domestica",
        INTERNATIONAL_SHARE: "Participacao internacional",
    }
    return labels.get(column, column)


def display_column_labels() -> dict[str, str]:
    return {
        WORLDWIDE: "Mundialmente",
        DOMESTIC: "EUA/Canada",
        DOMESTIC_SHARE: "EUA/Canada (%)",
        INTERNATIONAL: "Internacional",
        INTERNATIONAL_SHARE: "Internacional (%)",
    }


def get_top_row(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns and not df[column].isna().all():
        return df.loc[df[column].idxmax()]
    return df.iloc[0]


def format_money(value: float | int | pd.NA) -> str:
    if pd.isna(value):
        return "-"
    return f"${float(value):,.0f}"


def format_percent(value: float | int | pd.NA) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.1%}"


def safe_int(value: float | int | pd.NA, fallback: int) -> int:
    if pd.isna(value) or value <= 0:
        return fallback
    return int(value)

if __name__ == "__main__":
    render_dashboard()