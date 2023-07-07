import validators


def validate(url_in):
    errors = []
    if len(url_in) > 255:
        errors.append("URL превышает 255 символов")    
    if not validators.url(url_in):
        errors.append("Некорректный URL")
    if not url_in:
        errors.append("URL обязателен")    
    return errors
