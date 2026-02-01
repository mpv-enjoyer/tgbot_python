FROM python

RUN pip install python-telegram-bot
RUN mkdir /tgbot
WORKDIR /tgbot

ENTRYPOINT [ "python", "/tgbot/main.py" ]