class EnvironmentVariableError(Exception):
    """Исключение для случая с отсутствием необходимых переменных окружения."""

    pass


class ResponseTypeError(Exception):
    """Исключения для отличия типа данных ответа API от ожидаемого."""

    pass


class ResponseKeyError(Exception):
    """Исключение для отсутствия необходимого ключа в ответе API."""

    pass


class APIConnectionError(Exception):
    """Исключение для ошибки запроса к API."""

    pass
