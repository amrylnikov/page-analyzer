from bs4 import BeautifulSoup


def parse(request):
    code = request.status_code
    soup = BeautifulSoup(request.text, 'html.parser')
    title = soup.title.get_text()
    h1 = soup.h1.text if soup.h1 else ''
    description_tag = soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else ''
    return code, h1, title, description
