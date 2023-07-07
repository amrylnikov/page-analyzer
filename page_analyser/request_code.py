import requests
from bs4 import BeautifulSoup

r = requests.get('https://github.com')
print(r.status_code)
soup = BeautifulSoup(r.text, 'html.parser')
print(soup.title.get_text())
h1_tags = soup.find_all('h1')
for h1 in h1_tags:
    h1_text = h1.get_text()
    print(h1_text)
print('--------------------------')
meta_tags = soup.find_all('meta')
for meta in meta_tags:
    if meta.get('name') == 'description':
        site_description = meta.get('content')
        print(site_description)