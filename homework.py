import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot, TelegramError

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
START_TIME = 0


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s '
    '%(funcName)s:%(lineno)d %(message)s'
)
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)
file_handler = logging.FileHandler('./homework.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def send_message(bot, message):
    """Функция отправляет сообщение в чат."""
    try:
        logger.info('Попытка отправки сообщения {} в чат'.format(message))
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения в чат. {error}')
        return False
    else:
        logger.info('Сообщение {} отправлено в чат'.format(message))
        return True


def get_api_answer(current_timestamp):
    """Функция совершает запрос по API к endpoint."""
    data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': current_timestamp}
    }
    logger.info('Выполняем запрос к API c url:{url}, '
                'headers:{headers}, params:{params}'.format(**data))
    try:
        response = requests.get(**data)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.APIResponseStatusException(
                f'Неверный код ответа сервера. Код:{response.status_code}, '
                f'Причина:{response.reason}, Текст:{response.text}'
            )
        logger.info('Запрос по API прошел успешно')
        return response.json()
    except Exception as error:
        raise ConnectionError(
            'Ошибка при запросе по API к endpoint:{error} '
            'c параметрами url:{url}, headers:{headers}, '
            'params:{params}'.format(error=error, **data)
        )


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    logger.info('Выполняем проверку ответа API на корректность')
    if not isinstance(response, dict):
        message = 'В ответе API не словарь'
        logger.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        raise exceptions.EmptyResponseAPIException(
            'В ответе API нет домашних работ')
    homeworks_list = response.get('homeworks')
    if not isinstance(homeworks_list, list):
        raise ValueError(
            'В ответе API домашние работы представлены не списком')
    logger.info('Список домашних работ получен успешно')
    return homeworks_list


def parse_status(homework):
    """Функция проверяет статус домашней работы."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        message = 'Отсутсвует ключ homework_name в ответе API'
        logger.error(message)
        raise KeyError(message)
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Неизвестный статус {} домашней работы'.format(
            homework_status))
    logger.info('Проверка статуса домашней работы прошла успешно')
    return (
        'Изменился статус проверки работы "{homework_name}". '
        '{verdict}'.format(homework_name=homework_name,
                           verdict=HOMEWORK_VERDICTS[homework_status])
    )


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    names_tokens = (
        ('practicum_token', PRACTICUM_TOKEN),
        ('telegram_token', TELEGRAM_TOKEN),
        ('chat_id', TELEGRAM_CHAT_ID)
    )
    tokens_bool = True
    for name, token in names_tokens:
        if not token:
            logger.critical(
                'Переменная окружения {} недоступна'.format(name))
            tokens_bool = False
    return tokens_bool


def main():
    """Основная логика работы бота."""
    logger.info('Бот в работе')
    if not check_tokens():
        raise exceptions.MissingRequiredTokenException(
            'Необходимые переменные окружения недоступны')
    logger.info('Необходимые переменные окружения доступны')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = START_TIME
    current_report = {
        'name_messages': None
    }
    prev_report = {
        'name_messages': None
    }
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework_status = homeworks[0]
                message = parse_status(homework_status)
                current_report['name_messages'] = message
            else:
                current_report['name_messages'] = (
                    'Статус проверки домашней работы не изменился')
            if current_report != prev_report:
                if send_message(bot, current_report['name_messages']):
                    prev_report = current_report.copy()
                    if response.get('current_date'):
                        current_timestamp = response.get('current_date')
            else:
                logger.debug('Статус проверки домашней работы не изменился')

        except exceptions.EmptyResponseAPIException as error:
            logger.error(error, exc_info=True)

        except Exception as error:
            current_report['name_messages'] = (
                'Сбой в работе программы: {}'.format(error))
            if current_report != prev_report:
                send_message(bot, current_report['name_messages'])
                prev_report = current_report.copy()
            logger.error(error, exc_info=True)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
