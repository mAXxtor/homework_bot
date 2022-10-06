class SendMessageException(Exception):
    """Ошибки отправки сообщения."""

    pass


class APIResponseStatusException(Exception):
    """Ошибки запроса к API."""

    pass


class DictResponseException(Exception):
    """Ошибки в ответе API не словарь."""

    pass


class EmptyResponseAPIException(Exception):
    """Ошибки пустого ответа API."""

    pass


class HWResponseAPIException(Exception):
    """Ошибки не верного представления домашних работ в ответе API."""

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