import requests
from bs4 import BeautifulSoup

url = "https://m.danawa.com/product/product.html?code=88205561&keyword=%EC%A0%A4%EB%8B%A4%EC%9D%98+%EC%A0%84%EC%84%A4+%ED%8B%B0%EC%96%B4%EC%8A%A4+%EC%98%A4%EB%B8%8C+%EB%8D%94+%ED%82%B9%EB%8D%A4+%EC%8A%A4%EC%9C%84%EC%B9%982&cateCode=11338057"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

for meta in soup.find_all('meta'):
    if meta.get('property', '').startswith('og:') or meta.get('name', '').startswith('description'):
        print(meta)
