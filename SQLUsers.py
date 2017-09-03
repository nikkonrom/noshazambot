import sqlite3


class SQLUsers: 


    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def check_user(self, user_id):
        with self.connection:
            return self.cursor.execute('SELECT count(user_id)>0 FROM users WHERE user_id = ?', (user_id,)).fetchall()


    def write_user(self, user_id):
        with self.connection:
            self.cursor.execute('INSERT into users (user_id, score, rate) values (?, ?)', (user_id, 0))
    
    def edit_score(self, user_id, score):
        with self.connection:
            self.cursor.execute('UPDATE users SET score = score + ? WHERE user_id = ?', (score, user_id))

    def edit_winrate(self, user_id):
        with self.connection:
            self.cursor.execute('UPDATE users SET win = win + 1 WHERE user_id = ?', (user_id, ))
    
    def edit_loserate(self, user_id):
        with self.connection:
            self.cursor.execute('UPDATE users SET lose = lose + 1 WHERE user_id = ?', (user_id, ))
    
    def get_(self, parameter_list):
        pass

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.commit()
        self.connection.close()
    
    
    def get_top_players(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM users ORDER BY score DESC LIMIT 3').fetchall()
    

    def get_current_player_position(self, user_id):
        with self.connection:
            return self.cursor.execute('SELECT (SELECT COUNT(*) FROM users AS _t2 WHERE _t2.score>=_t1.score) AS pos,user_id,score FROM users AS _t1 WHERE user_id=?',(user_id,)).fetchall()