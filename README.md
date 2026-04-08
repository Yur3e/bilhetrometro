# Bilhetrometro

Dashboard em Streamlit para acompanhar a bilheteria mundial dos principais filmes listados no Box Office Mojo.

## Estrutura do projeto

```text
.
|-- app.py
|-- bilhetrometro.py
|-- dashboard.py
|-- services/
|   |-- __init__.py
|   `-- box_office.py
|-- assets/
|   `-- dashboard-preview.png
|-- README.md
`-- requirements.txt
```

## Funcionalidades

- Métricas principais de bilheteria mundial e doméstica.
- Gráfico interativo com ranking dos filmes.
- Filtros por quantidade de filmes e faixa de arrecadação.
- Tabela detalhada com os valores tratados para análise.

## Tecnologias

- Python
- Streamlit
- Pandas
- Altair
- NumPy
- Beautiful Soup

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

O arquivo `bilhetrometro.py` foi mantido como compatibilidade para execuções antigas.

## Fonte dos dados

Os dados são coletados diretamente da página de bilheteria mundial do Box Office Mojo no momento da execução.

## Prévia

![Bilhetrometro](assets/dashboard-preview.png)
