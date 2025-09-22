import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import requests
from bs4 import BeautifulSoup

# --- FUNÇÃO OTIMIZADA PARA PEGAR OS DADOS ---
@st.cache_data(ttl=3600) # Guarda os dados em cache por 1 hora
def get_data():
    """
    Extrai os dados do Box Office Mojo, limpa e retorna um DataFrame.
    Trabalha apenas em memória, com tratamento de erros melhorado.
    """
    try:
        URL = 'https://www.boxofficemojo.com/year/world/'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        table = soup.find('table')
        # --- ADICIONADO: Verificação para garantir que a tabela foi encontrada ---
        if table is None:
            st.error("Não foi possível encontrar a tabela de dados na página. O site pode ter alterado a sua estrutura.")
            return None

        rows = table.find_all('tr')
        data = []

        for row in rows[1:]:
            cols = row.find_all('td')
            if not cols:
                continue
            data.append({
                'rank': cols[0].get_text(strip=True),
                'title': cols[1].get_text(strip=True),
                'worldwide': cols[2].get_text(strip=True),
                'domestic': cols[3].get_text(strip=True),
                'foreign': cols[4].get_text(strip=True) # Corresponde à coluna "Domestic %" no site
            })
        
        if not data:
            st.warning("Não foram encontrados dados de filmes na tabela.")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # --- Limpeza dos Dados ---
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

        df['worldwide'] = df['worldwide'].apply(clean_monetary)
        df['domestic'] = df['domestic'].apply(clean_monetary)
        df['foreign'] = df['foreign'].apply(clean_percentage)
        
        df = df.rename(columns={
            'rank': 'Rank',
            'title': 'Título',
            'worldwide': 'Mundialmente',
            'domestic': 'EUA/Canadá',
            'foreign': 'EUA/Canadá (%)'
        })
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar os dados da web: {e}")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante a extração dos dados: {e}")
        return None

# -------------------- Título e Layout do Dashboard --------------------
st.set_page_config(layout="wide")

col_logo, col_titulo = st.columns([0.05, 0.95], gap="small")
with col_logo:
    st.image("https://emojipedia-us.s3.amazonaws.com/source/skype/289/clapper-board_1f3ac.png", width=80)
with col_titulo:
    st.title('Bilhetrometro')
    st.markdown('Visualize a bilheteira mundial dos principais filmes.')

st.divider()

# -------------------- Barra Lateral com Ações e Filtros --------------------
st.sidebar.header('Atualizar Bilheteria:')
if st.sidebar.button("Atualizar Dados da Web"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.header('Filtros do Dashboard')

df = get_data()

if df is None or df.empty:
    st.error("Não foi possível carregar os dados. Verifique a sua ligação ou tente atualizar mais tarde.")
else:
    num_filmes = st.sidebar.slider(
        'Selecione o número de filmes:',
        min_value=5, max_value=len(df), value=10, step=1
    )

    # --- NOVO: Tratamento de erro para o caso de não haver dados numéricos ---
    max_value_from_df = df['Mundialmente'].max()
    if pd.isna(max_value_from_df):
        st.warning("Não foi possível determinar a bilheteira máxima a partir dos dados atuais.")
        max_worldwide = 1000000000 # Usa um valor padrão
    else:
        max_worldwide = int(max_value_from_df)

    min_worldwide = 0
    worldwide_range = st.sidebar.slider(
        'Filtrar por valor de bilheteira:',
        min_value=min_worldwide, max_value=max_worldwide,
        value=(min_worldwide, max_worldwide)
    )
    
    with st.sidebar.expander("ℹ️ Sobre o Projeto"):
        st.write("""
            **Fonte dos Dados:** Box Office Mojo.
            **Desenvolvido por:** José Yure
            
            Este dashboard interativo foi construído com Streamlit para analisar
            as bilheteiras de filmes.
        """)

    # -------------------- Aplica os filtros e exibe o conteúdo --------------------
    df_filtrado = df[(df['Mundialmente'] >= worldwide_range[0]) & (df['Mundialmente'] <= worldwide_range[1])]
    df_filtrado_top_n = df_filtrado.nlargest(num_filmes, 'Mundialmente')

    st.header('Métricas Principais:')
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Bilheteira Mundial Total", value=f"${df_filtrado['Mundialmente'].sum():,.0f}")
    with col2:
        if not df_filtrado.empty and not df_filtrado['Mundialmente'].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado['Mundialmente'].idxmax()]
            st.metric(label=f"Maior Bilheteira Mundial ({top_movie['Título']})", value=f"${top_movie['Mundialmente']:,.0f}")
    with col3:
        if not df_filtrado.empty and not df_filtrado['EUA/Canadá'].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado['EUA/Canadá'].idxmax()]
            st.metric(label=f"Maior Bilheteira Doméstica ({top_movie['Título']})", value=f"${top_movie['EUA/Canadá']:,.0f}")
    with col4:
        if not df_filtrado.empty and not df_filtrado['EUA/Canadá (%)'].isnull().all():
            top_movie = df_filtrado.loc[df_filtrado['EUA/Canadá (%)'].idxmax()]
            st.metric(label=f"Maior % Bilheteira EUA/Canadá ({top_movie['Título']})", value=f"{top_movie['EUA/Canadá (%)'] * 100:.2f}%")

    st.header('Análise Visual dos Filmes:')
    tab1, tab2 = st.tabs(["📊 Gráfico de Barras", "📄 Tabela Detalhada"])

    with tab1:
        st.subheader(f'Top {num_filmes} Filmes por Bilheteira Mundial')
        if not df_filtrado_top_n.empty:
            chart = alt.Chart(df_filtrado_top_n).mark_bar().encode(
                x=alt.X('Mundialmente', title='Bilheteira Mundial ($)'),
                y=alt.Y('Título', sort='-x', title='Filme'),
                tooltip=['Título', alt.Tooltip('Mundialmente', format='$,.0f'), alt.Tooltip('EUA/Canadá', format='$,.0f')]
            ).properties(title=f'Top {num_filmes} Filmes por Bilheteira Mundial')
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("Nenhum filme encontrado com os filtros aplicados.")

    with tab2:
        st.subheader('Dados dos Filmes Selecionados')
        df_display = df_filtrado_top_n[['Rank', 'Título', 'Mundialmente', 'EUA/Canadá', 'EUA/Canadá (%)']]
        df_styled = df_display.style.format({
            'Mundialmente': '${:,.0f}',
            'EUA/Canadá': '${:,.0f}',
            'EUA/Canadá (%)': '{:.2%}'
        }).background_gradient(cmap='viridis', subset=['Mundialmente', 'EUA/Canadá'])
        st.dataframe(df_styled, hide_index=True, use_container_width=True)
        