import pandas as pd
from flask_login import UserMixin
from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, token, application, organization, domain_name):
        self.id = id_
        self.name = name
        self.email = email
        self.token = token
        self.application = application
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
            id_=user[0], name=user[1], email=user[2], token=user[3], application=user[4], organization=user[5], domain_name=user[6]
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
    def create(id_, name, email, token, application, organization, domain_name):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, token, application, organization, domain_name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_, name, email, token, application, organization, domain_name,),
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

    def update_field(cond_field, cond, table, field, data, path = None):
        db = get_db(path)
        query="UPDATE " + table + " SET " + field + "= ? WHERE " + cond_field + "= ?"
        db.execute(
           query, (data, cond), 
        )
        db.commit()

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

    # def update_fields(user_id, db, fields):
    #     db = get_db()
    #     query_1 = "UPDATE " + db + " SET " 
    #     query_3 = "= ? WHERE id = ?"
    #     query_2 = ""
    #     for i in fields:
    #         query_2 = query_2 + i + " = ? , "
    #     query_2 = query_2[:len(query_2) - 3]
    #     query = query_1 + query_2 + query_3
    #     print(query)
        
    #     db.execute(
    #       , fields 
    #     )
    #     db.commit()

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

    def fetch_applications():
        db = get_db()
        applications = db.execute(
            "SELECT application FROM user",
        ).fetchall()
        appList=[]
        for row in applications:
            appList.append(row[0])
        # remove duplicates
        appList = list(set(appList))
        return appList
       