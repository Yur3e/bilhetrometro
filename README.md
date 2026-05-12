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

- Metricas principais de bilheteria mundial, media por filme e peso domestico.
- Filtros por busca de titulo, quantidade no ranking, faixa de arrecadacao e participacao EUA/Canada.
- Cartoes de destaque para campeao mundial, maior forca domestica e filme mais internacional.
- Abas com ranking, composicao domestica/internacional, dispersao e tabela detalhada.
- Exportacao dos dados filtrados em CSV.

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

O arquivo `bilhetrometro.py` foi mantido como compatibilidade para execucoes antigas.

## Fonte dos dados

Os dados sao coletados diretamente da pagina de bilheteria mundial do Box Office Mojo no momento da execucao.

## Previa

![Bilhetrometro](assets/dashboard-preview.png)
