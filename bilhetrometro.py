import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import requests
from bs4 import BeautifulSoup
import csv
import os

# --- ADICIONADO: Função para extrair e salvar os dados da web integrado --- 
def atualizar_dados():
    """
    Função que extrai os dados do Box Office Mojo e salva em um arquivo CSV na pasta interna do programa.
    Esta função foi adaptada do script 'extrair_dados.py'.
    """
    with st.spinner('Atualizando dados a partir do Box Office Mojo, por favor aguarde...'):
        try:
            URL = 'https://www.boxofficemojo.com/year/world/'
            response = requests.get(URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table')
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
                    'foreign': cols[4].get_text(strip=True)
                })

            # Salva os dados no arquivo CSV na mesma pasta do script
            with open('bilhetrometro/boxoffice_2025_worldwide.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['rank', 'title', 'worldwide', 'domestic', 'foreign'])
                writer.writeheader()
                writer.writerows(data)
            
            st.success('Dados atualizados com sucesso!')
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao buscar os dados da web: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante a atualização: {e}")

# --- ADICIONADO: Função de carregamento de dados ---
@st.cache_data
def load_data():
    """Carrega e limpa o arquivo CSV. Retorna None se o arquivo não existir."""
    caminho_arquivo = "bilhetrometro/boxoffice_2025_worldwide.csv"
    if not os.path.exists(caminho_arquivo):
        return None
    
    df = pd.read_csv(caminho_arquivo)

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

# -------------------- Título e Layout do Dashboard --------------------
st.set_page_config(layout="wide")

col_logo, col_titulo = st.columns([0.05, 0.95], gap="small")
with col_logo:
    st.image("https://emojipedia-us.s3.amazonaws.com/source/skype/289/clapper-board_1f3ac.png", width=80) # Ícone para o título
with col_titulo:
    st.title('Bilhetrometro (2025)')
    st.markdown('Visualize a bilheteria de todos os filmes ranqueados até o TOP 1000.')

st.divider()

# -------------------- Barra Lateral com Ações e Filtros --------------------
st.sidebar.header('Ações')
if st.sidebar.button("Atualizar Dados da Web"):
    atualizar_dados()
    st.cache_data.clear() # Limpa o cache para recarregar os novos dados
    st.rerun()

st.sidebar.divider()
st.sidebar.header('Filtros do Dashboard')

df = load_data()

# --- MODIFICADO: Lógica para lidar com a ausência do arquivo de dados ---
if df is None:
    st.warning("Arquivo de dados 'boxoffice_2025_worldwide.csv' não encontrado.")
    st.info("Por favor, clique no botão 'Atualizar Dados da Web' na barra lateral para baixar os dados.")
else:
    num_filmes = st.sidebar.slider(
        'Selecione o número de filmes:',
        min_value=5, max_value=len(df), value=10, step=1
    )

    min_worldwide = 0
    max_worldwide = int(df['Mundialmente'].max())
    worldwide_range = st.sidebar.slider(
        'Filtrar por valor de bilheteria:',
        min_value=min_worldwide, max_value=max_worldwide,
        value=(min_worldwide, max_worldwide)
    )
    
    with st.sidebar.expander("ℹ️ Sobre o Projeto"):
        st.write("""
            **Fonte dos Dados:** Box Office Mojo (dados de 2025).
            **Desenvolvido por:** José Yure
            
            Este dashboard interativo foi construído com Streamlit para analisar
            as bilheterias de filmes.
        """)

    # -------------------- Aplica os filtros e exibe o conteúdo --------------------
    df_filtrado = df[(df['Mundialmente'] >= worldwide_range[0]) & (df['Mundialmente'] <= worldwide_range[1])]
    df_filtrado_top_n = df_filtrado.nlargest(num_filmes, 'Mundialmente')

    st.header('Métricas Principais')
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Bilheteria Mundial Total", value=f"${df_filtrado['Mundialmente'].sum():,.0f}")
    with col2:
        if not df_filtrado.empty:
            top_movie = df_filtrado.loc[df_filtrado['Mundialmente'].idxmax()]
            st.metric(label=f"Maior Bilheteria Mundial ({top_movie['Título']})", value=f"${top_movie['Mundialmente']:,.0f}")
    with col3:
        if not df_filtrado.empty:
            top_movie = df_filtrado.loc[df_filtrado['EUA/Canadá'].idxmax()]
            st.metric(label=f"Maior Bilheteria Doméstica ({top_movie['Título']})", value=f"${top_movie['EUA/Canadá']:,.0f}")
    with col4:
        if not df_filtrado.empty:
            top_movie = df_filtrado.loc[df_filtrado['EUA/Canadá (%)'].idxmax()]
            st.metric(label=f"Maior % Bilheteria EUA/Canadá ({top_movie['Título']})", value=f"{top_movie['EUA/Canadá (%)'] * 100:.2f}%")

    st.header('Análise Visual dos Filmes')
    tab1, tab2 = st.tabs(["📊 Gráfico de Barras", "📄 Tabela Detalhada"])

    with tab1:
        st.subheader(f'Top {num_filmes} Filmes por Bilheteria Mundial')
        if not df_filtrado_top_n.empty:
            chart = alt.Chart(df_filtrado_top_n).mark_bar().encode(
                x=alt.X('Mundialmente', title='Bilheteria Mundial ($)'),
                y=alt.Y('Título', sort='-x', title='Filme'),
                tooltip=['Título', alt.Tooltip('Mundialmente', format='$,.0f'), alt.Tooltip('EUA/Canadá', format='$,.0f')]
            ).properties(title=f'Top {num_filmes} Filmes por Bilheteria Mundial')
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
