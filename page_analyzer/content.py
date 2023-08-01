def get_seo_data_from_html(html):
    title = html.title.get_text()
    h1 = html.h1.text if html.h1 else ''
    description_tag = html.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else ''
    return h1, title, description
