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

@bot.message_handler(commands=['start'])
def start_guess(message):
    db_users_worker = SQLUsers(config.users_database_name)
    state = db_users_worker.check_user(message.from_user.first_name + ' ' + message.from_user.last_name)
    if state[0][0]:
        pass
    else:
        db_users_worker.write_user(message.from_user.first_name + ' ' + message.from_user.last_name)
        
    db_users_worker.close()
    markup_keyboard = utils.generate_main_markup()
    bot.send_message(message.chat.id, 'Начать игру - /track\nТаблица лидеров - /leaderboard', reply_markup = markup_keyboard)

@bot.message_handler(commands=['leaderboard'])
def send_leaderboard(message):
    db_users_worker = SQLUsers(config.users_database_name)
    top_players = db_users_worker.get_top_players()
    current_player = db_users_worker.get_current_player_position(message.from_user.first_name + ' ' + message.from_user.last_name)[0]
    db_users_worker.close()

    ladder_exists = 0
    text = []
    counter = 1
    

    for item in top_players:
        text.append(str(counter) + '. ' + item[0] + ' — ' + str(round(item[1], 1)))
        counter += 1
        if item[0] == current_player[1]:
            ladder_exists = 1   
    max
    
    if ladder_exists:
        message_text ='Congrats!\n' + '\n'.join(text)
    else:
        player_line = str(current_player[0]) + '. ' + current_player[1] + ' — ' + str(round(current_player[2],1))
        text.append(player_line)
        max_len = max(map(len, text))
        text.remove(text[3])
        message_text = '\n'.join(text) + '\n' + '. '*max_len + '\n' + player_line
    
    bot.send_message(message.chat.id, message_text)


    


@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    username = message.from_user.first_name + ' ' + message.from_user.last_name
    # Если функция возвращает None -> Человек не в игре
    answer = utils.get_answer_for_user(message.chat.id)
    # Как Вы помните, answer может быть либо текст, либо None
    # Если None:
    if not answer:
        bot.send_message(message.chat.id, 'Чтобы начать игру, выберите команду /track')
    else:
        db_users_worker = SQLUsers(config.users_database_name)
        markup_keyboard = utils.generate_main_markup()
        # Если ответ правильный/неправильный
        if message.text == answer[0]:
            elapsed_time = time.time() - answer[1]
            bonus_score = 0
            if elapsed_time < 21:
                bonus_score = (21 - elapsed_time)
            score = config.right_score + bonus_score            
            bot.send_message(message.chat.id, 'Верно! Вы получили {} очков (бонус за скорость: {})'.format(str(round(score)), str(round(bonus_score))), reply_markup=markup_keyboard)
            db_users_worker.edit_winrate(username)
            db_users_worker.edit_score(username, score)
        else:
            db_users_worker.edit_loserate(username)
            bot.send_message(message.chat.id, 'Увы, Вы не угадали. Попробуйте ещё раз!', reply_markup=markup_keyboard)
        db_users_worker.close()
        utils.finish_user_game(message.chat.id)

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
