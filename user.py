from flask_login import UserMixin

from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, token):
        self.id = id_
        self.name = name
        self.email = email
        self.token = token

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        
        user = User(
            id_=user[0], name=user[1], email=user[2], token=user[3]
        )
        return user

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
    def create(id_, name, email, token):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, token) "
            "VALUES (?, ?, ?, ?)",
            (id_, name, email, token),
        )
        db.commit()

    '''def delete_all():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM user")
        entries = cursor.fetchall()

        return print(entries)'''
       