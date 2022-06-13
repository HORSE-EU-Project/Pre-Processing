import pandas as pd
from flask_login import UserMixin
from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, token, organization, domain_name):
        self.id = id_
        self.name = name
        self.email = email
        self.token = token
        self.organization = organization
        self.domain_name = domain_name

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        
        user = User(
            id_=user[0], name=user[1], email=user[2], token=user[3], organization=user[4], domain_name=user[5]
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
    def create(id_, name, email, token, organization, domain_name):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, token, organization, domain_name) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_, name, email, token, organization, domain_name,),
        )
        db.commit()

    @staticmethod
    def insert_in_history(id_, timestamp, filename, description):
        db = get_db()
        db.execute(
            "INSERT INTO history (usr_id, timestamp, filename, description) "
            "VALUES (?, ?, ?, ?)",
            (id_, timestamp, filename, description,),
        )
        db.commit()

    def create_user_app(app, user, path=None):
        db = get_db(path)
        db.execute(
            "INSERT INTO apps (name, user) "
            "VALUES (?, ?)",
            (app, user,),
        )
        db.commit()

    def delete_app_user(user, app, path=None):
        db=get_db(path)
        query = "DELETE FROM apps WHERE user = ? and name = ?"
        db.execute(query, (user, app,))
        db.commit()

    def get_all(table, field, path=None):
        db = get_db(path)
        query = "SELECT " + field + " FROM " + table
        data = db.execute(query).fetchall()
        dataList=[]
        for row in data:
            dataList.append(row[0])
        # remove duplicates
        dataList = list(set(dataList))
        return dataList

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

    def update_field(cond_field, cond, table, field, data, path = None):
        db = get_db(path)
        query="UPDATE " + table + " SET " + field + "= ? WHERE " + cond_field + "= ?"
        db.execute(
           query, (data, cond,), 
        )
        db.commit()
        return

    def get_field(cond_field, cond, table, field, path=None):
        db = get_db(path)
        query = "SELECT " + field + " FROM " + table + " WHERE " + cond_field + "= ?"
        #query = "SELECT * FROM " + table
        data = db.execute(
            query, (cond,)
        ).fetchone()
        if data:
            data = data[0]
        else:
            return -1
        return data

    def add_app_org(user_id, application, organization):
        db = get_db()
        db.execute(
            "UPDATE user SET application = ?, organization = ? WHERE id = ?", (application, organization, user_id), 
        )
        db.commit()

    @staticmethod
    def get_app_org(user_id):
        db = get_db()
        app_org = db.execute(
            "SELECT application, organization FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        return [app_org[0], app_org[1]]