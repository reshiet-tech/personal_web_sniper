import requests
from bs4 import BeautifulSoup

url = "https://m.danawa.com/product/product.html?code=88205561"
headers = {"User-Agent": "TelegramBot (like TwitterBot)"}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

print("Meta tags for TelegramBot:")
for meta in soup.find_all('meta'):
    if meta.get('property', '').startswith('og:') or meta.get('name', '').startswith('description'):
        print(meta)
