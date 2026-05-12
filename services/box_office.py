import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

BOX_OFFICE_URL = "https://www.boxofficemojo.com/year/world/"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    )
}


class DataFetchError(RuntimeError):
    pass


@st.cache_data(ttl=3600)
def get_box_office_data() -> pd.DataFrame:
    try:
        response = requests.get(BOX_OFFICE_URL, headers=REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataFetchError(f"Erro ao buscar os dados da web: {exc}") from exc

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    if table is None:
        raise DataFetchError("Nao foi possivel encontrar a tabela de dados na pagina.")

    rows = table.find_all("tr")
    data = []

    for row in rows[1:]:
        cols = [col.get_text(strip=True) for col in row.find_all("td")]
        if len(cols) < 5:
            continue
        data.append(
            {
                "rank": cols[0],
                "title": cols[1],
                "worldwide": cols[2],
                "domestic": cols[3],
                "domestic_share": cols[4],
            }
        )

    if not data:
        return pd.DataFrame(
            columns=["Rank", "Titulo", "Mundialmente", "EUA/Canada", "EUA/Canada (%)"]
        )

    df = pd.DataFrame(data)
    df["worldwide"] = df["worldwide"].apply(clean_monetary)
    df["domestic"] = df["domestic"].apply(clean_monetary)
    df["domestic_share"] = df["domestic_share"].apply(clean_percentage)

    return df.rename(
        columns={
            "rank": "Rank",
            "title": "Titulo",
            "worldwide": "Mundialmente",
            "domestic": "EUA/Canada",
            "domestic_share": "EUA/Canada (%)",
        }
    )


def clean_monetary(value: str | float | int) -> float:
    if isinstance(value, str):
        normalized_value = value.replace("$", "").replace(",", "").strip()
        if normalized_value == "-":
            return np.nan
        return pd.to_numeric(normalized_value, errors="coerce")
    return value


def clean_percentage(value: str | float | int) -> float:
    if isinstance(value, str):
        normalized_value = value.replace("%", "").replace("<", "").strip()
        if normalized_value in {"-", ""}:
            return np.nan
        return pd.to_numeric(normalized_value, errors="coerce") / 100
    return value
