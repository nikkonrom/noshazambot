import telebot
import os
from flask import Flask, request
import config
import time
import utils
import random
from SQLighter import SQLighter
from SQLUsers import SQLUsers
from telebot import types


bot = telebot.TeleBot(config.bot_token)

server = Flask(__name__)

@bot.message_handler(commands=['track'])
def game(message):
    # Подключаемся к БД
    db_worker = SQLighter(config.music_database_name)
    # Получаем случайную строку из БД
    row = db_worker.select_single(random.randint(1, utils.get_rows_count()))
    # Формируем разметку
    markup = utils.generate_markup(row[2], row[3])
    # Отправляем аудиофайл с вариантами ответа
    bot.send_voice(message.chat.id, row[1], reply_markup=markup, timeout=10)
    # Включаем "игровой режим"
    utils.set_user_game(message.chat.id, row[2])
    # Отсоединяемся от БД
    db_worker.close()


@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    # Если функция возвращает None -> Человек не в игре
    answer = utils.get_answer_for_user(message.chat.id)
    # Как Вы помните, answer может быть либо текст, либо None
    # Если None:
    if not answer:
        bot.send_message(message.chat.id, 'Чтобы начать игру, выберите команду /track')
    else:
        markup_keyboard = utils.generate_main_markup()
        # Если ответ правильный/неправильный
        if message.text == answer[0]:
            elapsed_time = time.time() - answer[1]
            bonus_score = 0
            if elapsed_time < 21:
                bonus_score = (21 - elapsed_time)*10
            score = config.right_score + bonus_score            
            bot.send_message(message.chat.id, 'Верно! Вы получили {} очков, бонус за скорость: {}'.format(str(score), str(bonus_score)), reply_markup=markup_keyboard)
            db_worker = SQLUsers(config.users_database_name)
            db_worker.edit_score(message.chat.id, score)
            db_worker.close()
        else:
            bot.send_message(message.chat.id, 'Увы, Вы не угадали. Попробуйте ещё раз!', reply_markup=markup_keyboard)

        # Удаляем юзера из хранилища (игра закончена)
        utils.finish_user_game(message.chat.id)


@bot.message_handler(commands=['start'])
def start_guess(message):
    db_worker = SQLUsers(config.users_database_name)
    state = db_worker.check_user(message.chat.id)
    if state[0][0]:
        pass
    else:
        db_worker.write_user(message.chat.id)
        
    db_worker.close()
    markup_keyboard = utils.generate_main_markup()
    message = bot.send_message(message.chat.id, 'Начать игру - /track\nТаблица лидеров - /leaderboad', reply_markup = markup_keyboard)



@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://{}/bot".format(config.domain_name))
    return "!", 200

if __name__ == "__main__":
    utils.count_rows()
    random.seed()
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))
