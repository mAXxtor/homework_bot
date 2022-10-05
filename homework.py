import logging
import os
import time

import requests
from dotenv import load_dotenv
from http import HTTPStatus
from telegram import Bot

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
START_TIME = 3 * 30 * 24 * 60 * 60


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправляет сообщение в чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение в чат отправлено успешно')
    except exceptions.SendMessageException as error:
        logger.error(f'Ошибка при отправке сообщения в чат. {error}')


def get_api_answer(current_timestamp):
    """Функция совершает запрос по API к endpoint."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except exceptions.APIResponseStatusException as error:
        logger.error(f'Ошибка при запросе по API к endpoint. {error}')
    if response.status_code != HTTPStatus.OK:
        message = 'Неверный код ответ сервера'
        logger.error(message)
        raise exceptions.APIResponseStatusException(message)
    logger.info('Запрос по API прошел успешно')
    return response.json()


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    try:
        homeworks_list = response['homeworks']
    except KeyError as error:
        message = f'Ошибка доступа по ключу homeworks: {error}'
        logger.error(message)
        raise exceptions.CheckResponseException(message)
    if homeworks_list is None:
        message = 'В ответе API нет словаря с домашними работами'
        logger.error(message)
        raise exceptions.CheckResponseException(message)
    if not isinstance(homeworks_list, list):
        message = 'В ответе API домашние работы представлены не списком'
        logger.error(message)
        raise exceptions.CheckResponseException(message)
    if len(homeworks_list) == 0:
        message = 'За последний период выполненных домашних заданий нет'
        logger.info(message)
        raise exceptions.CheckResponseException(message)
    logger.info('Список домашних работ получен успешно')
    return homeworks_list


def parse_status(homework):
    """Функция проверяет статус домашней работы."""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as error:
        logger.error(f'Ошибка доступа по ключу homework_name: {error}')
    try:
        homework_status = homework.get('status')
    except KeyError as error:
        logger.error(f'Ошибка доступа по ключу status: {error}')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        message = 'Неизвестный статус домашней работы'
        logger.error(message)
        raise exceptions.EmptyHWNameOrStatus(message)
    logger.info('Проверка статуса домашней работы прошла успешно')
    return (f'Изменился статус проверки работы "{homework_name}".'
            f' {verdict}')


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    logger.info('Бот в работе')
    if not check_tokens():
        message = 'Необходимая переменная окружения не доступна'
        logger.critical(message)
        raise exceptions.MissingRequiredTokenException(message)
    logger.info('Необходимые переменные окружения доступны')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - START_TIME)
    previous_error = None
    previous_status = None
    while True:
        try:
            response = get_api_answer(current_timestamp)
        except exceptions.IncorrectAPIResponseException as error:
            if str(error) != previous_error:
                previous_error = str(error)
                send_message(bot, error)
            logger.error(error)
            time.sleep(RETRY_TIME)
            continue
        try:
            homeworks = check_response(response)
            homework_status = homeworks[0].get('status')
            if homework_status != previous_status:
                previous_status = homework_status
                message = parse_status(homeworks[0])
                logger.info(f'Статус проверки домашней работы '
                            f'{homeworks[0]["homework_name"]} изменился')
                send_message(bot, message)
            else:
                logger.debug('Статус проверки домашней работы не изменился')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if previous_error != str(error):
                previous_error = str(error)
                send_message(bot, message)
            logger.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
