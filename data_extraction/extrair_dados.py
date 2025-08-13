import requests
from bs4 import BeautifulSoup
import csv

URL = 'https://www.boxofficemojo.com/year/world/'

response = requests.get(URL)
response.raise_for_status()  # para garantir que a requisição deu certo
soup = BeautifulSoup(response.text, 'html.parser')

# Encontrar a tabela que contém os dados de "2025 Worldwide Box Office"
table = soup.find('table')


rows = table.find_all('tr')
data = []

for row in rows[1:]:  # pula o cabeçalho
    cols = row.find_all('td')
    if not cols:
        continue
    rank = cols[0].get_text(strip=True)
    title = cols[1].get_text(strip=True)
    worldwide = cols[2].get_text(strip=True)
    domestic = cols[3].get_text(strip=True)
    foreign = cols[4].get_text(strip=True)
    data.append({
        'rank': rank,
        'title': title,
        'worldwide': worldwide,
        'domestic': domestic,
        'foreign': foreign
    })

with open('boxoffice_2025_worldwide.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['rank','title','worldwide','domestic','foreign'])
    writer.writeheader()
    writer.writerows(data)
