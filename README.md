### Homework Bot

```
Телеграм-бот для отслеживания статуса проверки домашней работы на Яндекс.Практикум.
Присылает сообщения при изменениях статуса.
```

### Использованные Технологии:
- Python 3.7.9
- python-dotenv 0.19.0
- python-telegram-bot 13.7
- requests 2.26.0

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/mAXxtor/homework_bot.git
```
или
```
git clone git@github.com:mAXxtor/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Записать в переменные окружения (файл .env) необходимые ключи:
- токен профиля на Яндекс.Практикуме
- токен телеграм-бота (создать нового телеграм-бота можно с помощью @BotFather)
- свой ID в телеграме (узнать можно с помощью бота @userinfobot)
