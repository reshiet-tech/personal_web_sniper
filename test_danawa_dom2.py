import requests
from bs4 import BeautifulSoup

url = "https://m.danawa.com/product/product.html?code=88205561"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

print("Title:")
print(soup.title.text)

print("\nFinding elements with '최저':")
for el in soup.find_all(text=lambda t: t and '최저' in t):
    parent = el.parent
    if parent:
        classes = parent.get('class', [])
        print(f"Parent tag: {parent.name}, classes: {classes}, text: {parent.text.strip()[:100]}")
