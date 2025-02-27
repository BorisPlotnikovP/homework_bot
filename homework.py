from http import HTTPStatus
import os
import requests
import sys
import time
import logging.handlers

from dotenv import load_dotenv
import logging
from telebot import TeleBot

from exceptions import (EnvironmentVariableError, ResponseTypeError,
                        ResponseKeyError, APIConnectionError)


formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('YP_TOKEN')
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TG_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

# Индекс домашней работы
INDEX = 0

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

homework_key = 'homeworks'

date_key = 'current_date'

status_key = 'status'

homework_name_key = 'homework_name'

ANSWER_KEYS = [homework_key, date_key]


def check_tokens():
    """Проверяет доступность переменных окруженияю."""
    TOKENS = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    empty_tokens = []
    for var in TOKENS:
        if not TOKENS[var]:
            empty_tokens.append(var)
    return empty_tokens


def send_message(bot, message):
    """Отправляет сообщение пользователю в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(
            'Произошел сбой при отправке сообщения в telegram: %s', error
        )
    else:
        logger.debug('Сообщение успешно отправленно в telegram')


def get_api_answer(timestamp):
    """Отправляет запрос на ENDPOINT и вовзращает ответв формате json."""
    try:
        response = requests.get(
            ENDPOINT, params={'from_date': timestamp}, headers=HEADERS
        )
    except Exception as error:
        logger.error(
            'Произошла ошибка во время выполнения запроса к API: %s', error
        )
        raise APIConnectionError(
            'Произошла ошибка во время выполнения запроса к API. '
            'Проверьте логи приложения.'
        )
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        response_info = {
            'status_code': status_code,
            'headers': response.headers,
            'url': response.url,
            'elapsed_time': response.elapsed
        }
        logger.error('Произошла ошибка во время выполнения запроса к API: %s',
                     response_info)
        raise APIConnectionError(
            'Произошла ошибка во время выполнения запроса к API. '
            'Проверьте логи!'
        )
    return response.json()


def check_response(response):
    """Валидирует ответ API."""
    if isinstance(response, dict):
        logger.error('Тип данных ответа отличается от ожидаемого: dict, '
                     'получен: %s', type(response))
        raise TypeError('Тип данных ответа отличается от ожидаемого. '
                        'Проверьте логи!')
    for key in ANSWER_KEYS:
        if key not in response:
            logger.error('Отсутствует необходимый ключ в ответе api %s', key)
            raise ResponseKeyError(
                'В ответе API отсутствует необходимый ключ. '
                'Проверьте логи.'
            )
    homework_value = response.get(homework_key)
    if not isinstance(homework_value, list):
        logger.error('Получен неожиданный тип данных ключа %s: %s',
                     homework_key, type(homework_value))
        raise TypeError(
            'Тип данных домашней работы не соответствует ожидаемому.'
        )
    if not homework_value:
        logger.debug('Получен пустой список домашних работ!')


def parse_status(homework):
    """Валидирует статус дз и возвращает строку с вердиктом."""
    for key in homework_name_key, status_key:
        if key not in homework:
            logger.error('В полученной домашней работе отсутствует '
                         'необходимый ключ: %s', key)
            raise ResponseKeyError(
                'В ответе API отсутствует необходимый ключ. Проверьте логи!'
            )
    homework_status = homework[status_key]
    homework_name = homework[homework_name_key]
    if not homework_status or homework_status not in HOMEWORK_VERDICTS:
        logger.error(
            'Получен неожиданный статус домашней работы: %s', homework_status
        )
        raise ResponseTypeError(
            'Получен неожиданный статус домашней работы. Проверьте логи!'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    empty_tokens = check_tokens()
    if empty_tokens:
        logger.critical(
            'Отсутствуют необходимые переменные окружения: %s', empty_tokens
        )
        raise EnvironmentVariableError(
            f'Отсутствуют необходимые переменные окружения: {empty_tokens}'
        )
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status = None
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        else:
            homeworks = response.get('homeworks')
            if homeworks:
                new_status = parse_status(homeworks[INDEX])
                if new_status != current_status:
                    send_message(bot, new_status)
                    current_status = new_status
                else:
                    logger.debug('Статус полученной домашней работы '
                                 'не был изменен.')
                timestamp = response.get('current_date')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
