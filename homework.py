import logging.handlers
import os
import sys
import requests

from telebot import TeleBot

from dotenv import load_dotenv

import time

import logging

from http import HTTPStatus

from exceptions import EnvironmentVariableError


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


def check_tokens():
    """Проверяет доступность переменных окруженияю."""
    for var in TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, PRACTICUM_TOKEN:
        if not var:
            logger.critical(
                f'Отсутствует обязательная переменная окружения: {var}.'
                f'Программа остановлена.',
            )
            raise EnvironmentVariableError()


def send_message(bot, message):
    """Отправляет сообщение пользователю в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(
            f'Произошел сбой при отправке сообщения в telegram: {error}'
        )
    else:
        logger.debug('Сообщение успешно отправленно в telegram')


def get_api_answer(timestamp):
    """Отправляет запрос на ENDPOINT и вовзращает ответв формате json."""
    try:
        response = requests.get(
            ENDPOINT, params={'from_date': timestamp}, headers=HEADERS
        )
    except Exception:
        logger.error('Произошла ошибка во время выполнения запроса к API')
        raise ConnectionError(
            'Произошла ошибка во время выполнения запроса к API'
        )
    if response.status_code != HTTPStatus.OK:
        logger.error('Произошла ошибка во время выполнения запроса к API')
        raise ConnectionError(
            'Произошла ошибка во время выполнения запроса к API'
        )
    formated_response = response.json()
    return formated_response


def check_response(response):
    """Валидирует ответ API."""
    if not isinstance(response, dict):
        raise TypeError
    if 'homeworks' not in response:
        logger.error('Отсутствуют необходимые ключи в ответе api!')
        raise KeyError
    if not isinstance(response.get('homeworks'), list):
        logger.error('sdgjfdgkdjf')
        raise TypeError
    if not response.get('homework'):
        logger.debug('Получен пустой список домашних работ!')


def parse_status(homework):
    """Валидирует статус дз и возвращает строку с вердиктом."""
    homework_name = homework.get('homework_name')
    if not homework_name or 'status' not in homework:
        raise TypeError
    status = homework.get('status')
    if not status or status not in HOMEWORK_VERDICTS:
        raise TypeError
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
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
                send_message(bot, new_status)
                timestamp = response.get('current_date')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
