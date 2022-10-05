class SendMessageException(Exception):
    """Ошибки отправки сообщения."""

    pass


class APIResponseStatusException(Exception):
    """Ошибки запроса к API."""

    pass


class CheckResponseException(Exception):
    """Ошибки неверного формата ответа API."""

    pass


class EmptyHWNameOrStatus(Exception):
    """Ошибки ключей имени или статуса домашнего задания."""

    pass


class MissingRequiredTokenException(Exception):
    """Ошибки отсутствия необходимых переменных окружения."""

    pass


class IncorrectAPIResponseException(Exception):
    """Ошибки некорректного ответа API."""

    pass


class UnknownHWStatusException(Exception):
    """Ошибки неизвестного статуса домашнего задания."""

    pass