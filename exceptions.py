class APIResponseStatusException(Exception):
    """Ошибки запроса к API."""

    pass


class EmptyResponseAPIException(Exception):
    """Ошибки пустого ответа API."""

    pass


class MissingRequiredTokenException(Exception):
    """Ошибки отсутствия необходимых переменных окружения."""

    pass