import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# -------------------- Limpeza dos Dados --------------------
@st.cache_data
def load_data():
    """Carrega e limpa o arquivo CSV."""
    df = pd.read_csv("boxoffice_2025_worldwide.csv")

    # Funções de limpeza para os valores monetários e de porcentagem
    def clean_monetary(value):
        if isinstance(value, str):
            return pd.to_numeric(value.replace('$', '').replace(',', ''), errors='coerce')
        return value

    def clean_percentage(value):
        if isinstance(value, str):
            if value == '-':
                return np.nan
            return pd.to_numeric(value.replace('%', ''), errors='coerce') / 100
        return value

    # Aplica as funções de limpeza
    df['worldwide'] = df['worldwide'].apply(clean_monetary)
    df['domestic'] = df['domestic'].apply(clean_monetary)
    df['foreign'] = df['foreign'].apply(clean_percentage)
    
    # Renomeando colunas
    df = df.rename(columns={
        'rank': 'Rank',
        'title': 'Título',
        'worldwide': 'Mundialmente',
        'domestic': 'EUA/Canadá',
        'foreign': 'EUA/Canadá (%)'
    })
    
    return df

df = load_data()

# -------------------- Título e Layout do Dashboard --------------------
st.set_page_config(layout="wide")
st.title('🎬 Bilhetrometro (2025)')
st.markdown('Visualize a bilheteria de todos os filmes ranqueados até o TOP 1000.')

# -------------------- Barra Lateral com Filtros --------------------
st.sidebar.header('Filtros do Dashboard')
num_filmes = st.sidebar.slider(
    'Selecione o número de filmes:',
    min_value=5, max_value=1000, value=10, step=1
)

min_worldwide = 0
max_worldwide = int(df['Mundialmente'].max())
worldwide_range = st.sidebar.slider(
    'Filtre por Bilheteria Mundial:',
    min_value=min_worldwide, max_value=2_000_000_000,
    value=(min_worldwide, max_worldwide)
)

# -------------------- Aplica os filtros nos dados --------------------
df_filtrado = df[
    (df['Mundialmente'] >= worldwide_range[0]) & (df['Mundialmente'] <= worldwide_range[1])
]
df_filtrado_top_n = df_filtrado.nlargest(num_filmes, 'Mundialmente')

# -------------------- Métricas Chave --------------------
st.header('Métricas Principais')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Bilheteria Mundial Total",
        value=f"${df_filtrado['Mundialmente'].sum():,.0f}"
    )
with col2:
    if not df_filtrado.empty:
        top_worldwide_movie = df_filtrado.loc[df_filtrado['Mundialmente'].idxmax()]
        st.metric(
            label=f"Maior Bilheteria Mundial ({top_worldwide_movie['Título']})",
            value=f"${top_worldwide_movie['Mundialmente']:,.0f}"
        )
    else:
        st.metric(label="Maior Bilheteria Mundial", value="N/A")

with col3:
    if not df_filtrado.empty:
        top_domestic_movie = df_filtrado.loc[df_filtrado['EUA/Canadá'].idxmax()]
        st.metric(
            label=f"Maior Bilheteria Doméstica ({top_domestic_movie['Título']})",
            value=f"${top_domestic_movie['EUA/Canadá']:,.0f}"
        )
    else:
        st.metric(label="Maior Bilheteria Doméstica", value="N/A")
with col4:
    if not df_filtrado.empty:
        top_foreign_pct_movie = df_filtrado.loc[df_filtrado['EUA/Canadá (%)'].idxmax()]
        st.metric(
            label=f"Maior Bilheteria EUA/Canadá ({top_foreign_pct_movie['Título']})",
            value=f"{top_foreign_pct_movie['EUA/Canadá (%)'] * 100:.2f}%"
        )
    else:
        st.metric(label="Maior Bilheteria Estrangeira", value="N/A")

# -------------------- Gráfico de Visualização Int. --------------------
st.header('Gráfico de Barras Interativo')

if not df_filtrado_top_n.empty:
    chart = alt.Chart(df_filtrado_top_n).mark_bar().encode(
        x=alt.X('Mundialmente', title='Bilheteria Mundial ($)'),
        y=alt.Y('Título', sort='-x', title='Filme'),
        tooltip=['Título', alt.Tooltip('Mundialmente', format='$,.0f')]
    ).properties(
        title=f'Top {num_filmes} Filmes por Bilheteria Mundial'
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("Nenhum filme encontrado com os filtros aplicados.")

# -------------------- Tabela Interativa --------------------
st.header('Tabela de Filmes')
df_display = df_filtrado_top_n[['Rank', 'Título', 'Mundialmente', 'EUA/Canadá', 'EUA/Canadá (%)']]
df_styled = df_display.style.format({
    'Mundialmente': '${:,.0f}',
    'EUA/Canadá': '${:,.0f}',
    'EUA/Canadá (%)': '{:.2%}'
})

st.dataframe(df_styled, hide_index=True, use_container_width=True)