import validators


def validate(url):
    errors = []
    if len(url) > 255:
        errors.append("URL превышает 255 символов")
    if not validators.url(url):
        errors.append("Некорректный URL")
    if not url:
        errors.append("URL обязателен")
    return errors
