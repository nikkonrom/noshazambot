import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import config
import json
import time
import sqlite3
import codecs
import ffmpy
import telebot
from telebot import types


def get_list(id):
    offset = '0'
    
    api_query = 'http://api.xn--41a.ws/api.php?method=by_owner&owner_id=' + id + '&key=' + config.audio_api_key + '&offset=' + offset
    api_callback = requests.get(api_query)
    parsed_string = json.loads(api_callback.text)

    audios_count = parsed_string.get('totalCount')
    audio_list = parsed_string.get('list')

    api_query = 'http://api.xn--41a.ws/api.php?method=by_owner&owner_id=' + id + '&key=' + config.audio_api_key + '&offset=' + str(parsed_string.get('nextOffset'))
    api_callback = requests.get(api_query)
    parsed_string = json.loads(api_callback.text)
        
    audio_list.extend(parsed_string.get('list'))
    
    return audio_list


def validate_list(audio_list):
    driver = webdriver.Chrome()   
    driver.get('http://vk.com/')
    # Находим элементы формы и вводим данные для авторизации
    user_input = driver.find_element_by_xpath('/html/body/div[9]/div/div/div[2]/div[2]/div[3]/div/div/div/div[1]/div[1]/form/input[7]')
    user_input.send_keys(config.log)
    password_input = driver.find_element_by_xpath('/html/body/div[9]/div/div/div[2]/div[2]/div[3]/div/div/div/div[1]/div[1]/form/input[8]')
    password_input.send_keys(config.password)

    # Нажимаем на кнопку
    submit = driver.find_element_by_xpath('/html/body/div[9]/div/div/div[2]/div[2]/div[3]/div/div/div/div[1]/div[1]/form/button')
    submit.click()
    time.sleep(5)

    counter = 0
    for audio in list(audio_list):

        url = 'https://vk.com/audios' + config.user_id + '?audio_id=' + str(audio[1]) + '_' + str(audio[0]) + '&section=recoms_audio'
        driver.get(url)

        audio_sample = (driver.find_elements_by_class_name('audio_row__performer_title'))[:3:]
                
        if audio_sample and audio[5] < 600:
            result_string = ''

            for element in audio_sample:
                result_string += element.text.replace('\n', ' — ') + ','
            result_string = result_string[0:-1]
            audio_list[counter][8] = result_string
        else:
            audio_list.remove(audio)
            counter -= 1
        counter += 1
    driver.close()
    with open('validated_list.txt', 'w') as outfile:
        json.dump(audio_list, outfile)
    return audio_list

def upload_list(audio_list):
    bot = telebot.TeleBot(config.bot_token)
    filename_mp3 = 'temp.mp3'
    filename_ogg = 'temp.ogg'    
    counter = 0
    start = time.time()

    for audio in list(audio_list):
        try:
            
            api_query = 'http://api.я.ws/api.php?method=get.audio&ids=' + str(audio[1]) + '_' + str(audio[0]) + '&key=' + config.audio_api_key
            api_callback = requests.get(api_query)
            if api_callback.text == 'wrong ids or Limit exceeded(10)' or api_callback.status_code != 200:
                audio_list.remove(audio)
                continue
            audio_url = (json.loads(api_callback.text))[0][2]
            if get_local_ogg(audio_url, filename_mp3, filename_ogg):
                audio_list.remove(audio)
                continue        

            stop = time.time()
            if stop - start < 1:    #avoiding of exeption: 'Too many requests'
                time.sleep(1)
            start = stop

            audio_file_id = upload_ogg(bot, filename_ogg)
            audio[11] = audio_file_id
            os.remove(filename_ogg)   
        except:
            audio_list.remove(audio)
            if os.path.exists(filename_ogg):
                os.remove(filename_ogg)
            continue
        
    with open('uploaded_list.txt', 'w') as outfile:
        json.dump(audio_list, outfile)
    return audio_list

def download_mp3(audio_url, filename):
    audio_data = requests.get(audio_url)
    
    if audio_data.status_code != 200:
        return 1
    with open(filename, 'wb') as f:
        f.write(audio_data.content)
    return 0

def get_local_ogg(audio_url, filename_mp3, filename_ogg):
    if download_mp3(audio_url, filename_mp3):
        return 1
    ffmpeg_instance = ffmpy.FFmpeg(inputs = {filename_mp3 : '-ss 00:00:40.00 -t 20 '},
        outputs = {filename_ogg : ' -ac 2 -max_muxing_queue_size 1000'})
    ffmpeg_instance.cmd
    ffmpeg_instance.run()
    return 0


def upload_ogg(bot, filename_ogg):
    file = open(filename_ogg, 'rb')
    message = bot.send_voice(config.admin_chat_id, file, None, timeout = 10)
    file_id = message.voice.file_id
    return file_id

def update_database(audio_list):
    connection = sqlite3.connect('E:\proga\python\Bot2\Bot2\music_database.db')
    cursor = connection.cursor()
    cursor.execute("select max(id) as id from music")
    max_id = cursor.fetchone()[0]

    for audio in audio_list:
        max_id += 1
        right_answer = audio[4] + ' — ' + audio[3]
        cursor.execute("insert into music (id, file_id, right_answer, wrong_answers) values (?, ?, ?, ?) ", (max_id, audio[11], right_answer, audio[8]))

    connection.commit()
    connection.close()


#update_database(audio_list = (json.loads((codecs.open('uploaded_list.txt', 'r','utf_8_sig')).read())))
#update_database(upload_list(audio_list = (json.loads((codecs.open('validated_list.txt', 'r','utf_8_sig')).read()))))
update_database(upload_list(validate_list(get_list('72986467')))) #TYPE HERE VK ID OF PERSON, WHOSE AUDIOS YOU WANT TO ADD IN DATABASE OR CREATE A LOOP WITH ARRAY OF ID'S











