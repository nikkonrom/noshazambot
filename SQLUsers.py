import sqlite3


class SQLUsers: 


    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def check_user(self, chat_id):
        with self.connection:
            return self.cursor.execute('SELECT count(user_id)>0 FROM table WHERE id = {}'.format(chat_id)).fetchall()


    def write_user(self, chat_id):
        with self.connection:
            self.cursor.execute('INSERT into users (user_id, score) values ({}, {})'.format(str(chat_id), str(0)))
    
    def edit_score(self, chat_id, score):
        with self.connection:
            self.cursor.execute('UPDATE music SET score = score + {} WHERE user_id = {}', str(score), str(chat_id))
    
