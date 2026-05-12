from __future__ import annotations

from dataclasses import dataclass

import altair as alt
import pandas as pd
import streamlit as st

from services.box_office import DataFetchError, get_box_office_data


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
        page_title="Bilhetrometro",
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
    render_spotlight(filtered_df)
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
    prepared["Rank"] = pd.to_numeric(prepared["Rank"], errors="coerce")
    prepared[TITLE] = prepared[TITLE].fillna("Sem titulo")
    return prepared.sort_values(WORLDWIDE, ascending=False)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bilhete-bg: #f7f8fb;
            --bilhete-surface: #ffffff;
            --bilhete-border: #dfe4ea;
            --bilhete-ink: #172033;
            --bilhete-muted: #667085;
            --bilhete-primary: #0f766e;
            --bilhete-accent: #dc6803;
        }

        .stApp {
            background:
                linear-gradient(180deg, rgba(15, 118, 110, 0.08), rgba(255,255,255,0) 260px),
                var(--bilhete-bg);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        [data-testid="stMetric"] {
            background: var(--bilhete-surface);
            border: 1px solid var(--bilhete-border);
            border-radius: 8px;
            padding: 1rem;
            min-height: 118px;
            box-shadow: 0 8px 24px rgba(16, 24, 40, 0.04);
        }

        [data-testid="stMetricLabel"] p {
            color: var(--bilhete-muted);
            font-size: 0.88rem;
            line-height: 1.2;
        }

        [data-testid="stMetricValue"] {
            color: var(--bilhete-ink);
            font-size: clamp(1.35rem, 2vw, 2rem);
        }

        .hero {
            background: linear-gradient(135deg, #132238 0%, #0f766e 58%, #f59e0b 100%);
            color: white;
            border-radius: 8px;
            padding: clamp(1.25rem, 4vw, 2.25rem);
            margin-bottom: 1.25rem;
            box-shadow: 0 18px 40px rgba(16, 24, 40, 0.14);
        }

        .hero h1 {
            font-size: clamp(2rem, 6vw, 4.2rem);
            line-height: 0.98;
            margin: 0 0 0.75rem;
        }

        .hero p {
            margin: 0;
            color: rgba(255, 255, 255, 0.84);
            max-width: 780px;
            font-size: clamp(1rem, 2vw, 1.15rem);
        }

        .spotlight {
            background: var(--bilhete-surface);
            border: 1px solid var(--bilhete-border);
            border-radius: 8px;
            padding: 1rem;
            height: 100%;
        }

        .spotlight strong {
            color: var(--bilhete-ink);
            display: block;
            font-size: 1.05rem;
            line-height: 1.3;
            margin-bottom: 0.35rem;
        }

        .spotlight span {
            color: var(--bilhete-muted);
            display: block;
            font-size: 0.92rem;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
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
                Um painel interativo para explorar arrecadacao mundial, peso domestico
                e desempenho internacional dos principais filmes no Box Office Mojo.
                Agora analisando <strong>{visible_movies}</strong> de
                <strong>{total_movies}</strong> filmes filtrados, somando
                <strong>{format_money(total_worldwide)}</strong>.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(df: pd.DataFrame) -> DashboardFilters:
    st.sidebar.header("Controles")
    if st.sidebar.button("Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("Filtros")

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

    st.subheader("Destaques")
    col1, col2, col3 = st.columns(3)
    with col1:
        spotlight_card(
            "Campeao mundial",
            top_worldwide[TITLE],
            f"{format_money(top_worldwide[WORLDWIDE])} no total global",
        )
    with col2:
        spotlight_card(
            "Maior forca domestica",
            top_domestic[TITLE],
            f"{format_money(top_domestic[DOMESTIC])} nos EUA/Canada",
        )
    with col3:
        spotlight_card(
            "Mais internacional",
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
    st.subheader("Analise visual")
    tab_ranking, tab_mix, tab_scatter, tab_table = st.tabs(
        ["Ranking", "Composicao", "Dispersao", "Tabela"]
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
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X(f"{sort_column}:Q", title=format_column_label(sort_column)),
            y=alt.Y(f"{TITLE}:N", sort="-x", title=None),
            color=alt.Color(
                f"{INTERNATIONAL_SHARE}:Q",
                scale=alt.Scale(scheme="tealblues"),
                legend=alt.Legend(title="Peso internacional"),
            ),
            tooltip=movie_tooltips(),
        )
        .properties(height=max(320, top_n * 34))
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
                scale=alt.Scale(range=["#dc6803", "#0f766e"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip(f"{TITLE}:N", title="Filme"),
                alt.Tooltip("Mercado:N"),
                alt.Tooltip("Bilheteria:Q", title="Bilheteria", format="$,.0f"),
            ],
        )
        .properties(height=max(320, top_n * 34))
    )
    st.altair_chart(chart, use_container_width=True)


def render_scatter_chart(filtered_df: pd.DataFrame) -> None:
    chart_df = filtered_df.dropna(subset=[DOMESTIC, INTERNATIONAL, WORLDWIDE])
    if chart_df.empty:
        st.info("Sem dados suficientes para o grafico de dispersao.")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_circle(opacity=0.78)
        .encode(
            x=alt.X(f"{DOMESTIC}:Q", title="EUA/Canada", axis=alt.Axis(format="$~s")),
            y=alt.Y(
                f"{INTERNATIONAL}:Q",
                title="Internacional",
                axis=alt.Axis(format="$~s"),
            ),
            size=alt.Size(f"{WORLDWIDE}:Q", title="Mundialmente", legend=None),
            color=alt.Color(
                f"{DOMESTIC_SHARE}:Q",
                scale=alt.Scale(scheme="orangered"),
                legend=alt.Legend(title="Peso domestico"),
            ),
            tooltip=movie_tooltips(),
        )
        .interactive()
        .properties(height=460)
    )
    st.altair_chart(chart, use_container_width=True)


def render_table(filtered_df: pd.DataFrame, filters: DashboardFilters) -> None:
    table_df = filtered_df.sort_values(
        SORT_OPTIONS[filters.sort_label],
        ascending=False,
        na_position="last",
    )[
        [
            "Rank",
            TITLE,
            WORLDWIDE,
            DOMESTIC,
            DOMESTIC_SHARE,
            INTERNATIONAL,
            INTERNATIONAL_SHARE,
        ]
    ]
    display_df = table_df.rename(columns=display_column_labels())
    st.dataframe(
        display_df.style.format(
            {
                "Rank": "{:.0f}",
                "Mundialmente": "${:,.0f}",
                "EUA/Canada": "${:,.0f}",
                "EUA/Canada (%)": "{:.1%}",
                "Internacional": "${:,.0f}",
                "Internacional (%)": "{:.1%}",
            },
            na_rep="-",
        ).background_gradient(
            cmap="viridis",
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
