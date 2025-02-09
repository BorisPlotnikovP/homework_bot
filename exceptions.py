class EnvironmentVariableError(Exception):
    """Исключение для случая с отсутствием необходимых переменных окружения."""

    def __init__(self):
        pass

    def __str__(self):
        return 'Отсутствует необходимая переменная окружения'
