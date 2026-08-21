import requests
from bs4 import BeautifulSoup
import json

url = "https://www.yeogi.com/domestic-accommodations/6578?checkIn=2026-08-15&checkOut=2026-08-16&personal=8"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

for script in soup.find_all("script", type="application/ld+json"):
    print("JSON-LD found:")
    try:
        data = json.loads(script.string)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error parsing JSON:", e)
