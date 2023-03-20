import telebot
from telebot import types
import randomfile

bot = telebot.TeleBot('6060195927:AAET9G5KPe81tcUJL_yBs671RGQCmrteMaw')

randomfile.main(bot)


def main():
    bot.infinity_polling()


if __name__ == '__main__':
    main()
