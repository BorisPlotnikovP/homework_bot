class EnvironmentVariableError(Exception):
    """Исключение для случая с отсутствием необходимых переменных окружения."""
    pass


class ResponseTypeError(Exception):
    """Исключения для случая, когда тип данных в ответе отличается от ожидаемого"""
    pass


class ResponseKeyError(Exception):
    """Исключение для случая когда в ответе отсутствует необходимый для работы ключ"""
    pass


class APIConnectionError(Exception):
    """Исключение для ошибки подключения со стороны API"""
    pass