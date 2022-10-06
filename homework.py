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
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)
file_handler = logging.FileHandler(filename='./log/homework.log')
logger.addHandler(file_handler)


def send_message(bot, message):
    """Функция отправляет сообщение в чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Попытка отправки сообщения в чат')
    except TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения в чат. {error}')
        return False
    else:
        logger.info('Сообщение в чат отправлено')
        return True


def get_api_answer(current_timestamp):
    """Функция совершает запрос по API к endpoint."""
    timestamp = current_timestamp
    data = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
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
        message = ('Ошибка при запросе по API к endpoint:{error} '
                   'c параметрами url:{url}, headers:{headers}, '
                   'params:{params}'.format(error=error, **data))
        logger.error(message)
        raise ConnectionError(message)


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    logger.info('Выполняем проверку ответа API на корректность')
    if not isinstance(response, dict):
        message = 'В ответе API не словарь'
        logger.error(message)
        raise exceptions.DictResponseException(message)
    if response['homeworks'] is None:
        message = 'В ответе API нет домашних работ'
        logger.error(message)
        raise exceptions.EmptyResponseAPIException(message)
    homeworks_list = response.get('homeworks')
    if not isinstance(homeworks_list, list):
        message = 'В ответе API домашние работы представлены не списком'
        logger.error(message)
        raise exceptions.HWResponseAPIException(message)
    logger.info('Список домашних работ получен успешно')
    return homeworks_list


def parse_status(homework):
    """Функция проверяет статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        message = 'Неизвестный статус домашней работы'
        logger.error(message)
        raise exceptions.UnknownHWStatusException(message)
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
        if token is None:
            logger.critical('Переменная окружения {} недоступна'.format(name))
            tokens_bool = False
    return tokens_bool


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        format=('%(asctime)s [%(levelname)s] '
                '%(name)s %(funcName)s:%(lineno)d %(message)s'),
        level=logging.INFO,
    )
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
            if len(homeworks) != 0:
                homework_status = homeworks[0]
                message = parse_status(homework_status)
                current_report['name_messages'] = message
            else:
                current_report['name_messages'] = 'Статус проверки домашней работы не изменился'
            if current_report != prev_report:
                if send_message(bot, current_report['name_messages']):
                    prev_report = current_report.copy()
                    current_timestamp = response.get('current_date')
            else:
                logger.debug('Статус проверки домашней работы не изменился')

        except exceptions.EmptyResponseAPIException as error:
                logger.error(error)

        except Exception as error:
            current_report['name_messages'] = 'Сбой в работе программы: {}'.format(error)
            if current_report != prev_report:
                send_message(bot, current_report['name_messages'])
                prev_report = current_report.copy()

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
