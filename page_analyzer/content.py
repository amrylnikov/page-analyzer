from bs4 import BeautifulSoup


def get_seo_data_from_html(text):
    soup = BeautifulSoup(text, 'html.parser')
    title = soup.title.get_text()
    h1 = soup.h1.text if soup.h1 else ''
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else ''
    return h1, title, description
