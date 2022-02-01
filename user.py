import pandas as pd
from flask_login import UserMixin
from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, token, application):
        self.id = id_
        self.name = name
        self.email = email
        self.token = token
        self.application = application

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        
        user = User(
            id_=user[0], name=user[1], email=user[2], token=user[3], application=user[4]
        )
        return user
    
    @staticmethod
    def delete_per_id(id_):
        db = get_db()
        db.execute(
            "DELETE FROM user WHERE id = ?", (id_,)
        )
     
        db.commit()

    @staticmethod
    def updateToken(user_id, token):
        db = get_db()
        db.execute(
            "UPDATE user SET token = ? WHERE id = ?", (token, user_id), 
        )
        db.commit()
        '''
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
      
        user = User(
            id_=user[0], name=user[1], email=user[2], token=user[3]
        )
        return user
        '''
        return
    
    @staticmethod
    def get_token(user_id):
        db = get_db()
        token = db.execute(
            "SELECT token FROM user WHERE id = ?", (user_id,)
        ).fetchone()[0]
        return token

    @staticmethod
    def create(id_, name, email, token, application):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, token, application) "
            "VALUES (?, ?, ?, ?, ?)",
            (id_, name, email, token, application),
        )
        db.commit()

    @staticmethod
    def insert_in_history(id_, timestamp, filename, description):
        db = get_db()
        db.execute(
            "INSERT INTO history (usr_id, timestamp, filename, description) "
            "VALUES (?, ?, ?, ?)",
            (id_, timestamp, filename, description),
        )
        db.commit()

    def get_history(user_id):
        db = get_db()
        history_data = db.execute(
            "SELECT timestamp FROM history WHERE usr_id = ?", (user_id,)
        ).fetchall()
        return history_data

    def fetch_history_dataframe(user_id):
        db = get_db()
        history_data = pd.read_sql_query(
            "SELECT timestamp, filename, description FROM history WHERE usr_id = ?", db, params=(user_id,)
        )
        return history_data

    def add_app(user_id, application):
        db = get_db()
        db.execute(
            "UPDATE user SET application = ? WHERE id = ?", (application, user_id), 
        )
        db.commit()

    '''def delete_all():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM user")
        entries = cursor.fetchall()

        return print(entries)'''
       