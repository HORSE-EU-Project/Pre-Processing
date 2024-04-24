import pandas as pd
from flask_login import UserMixin
from db import get_db
import sqlite3
import subscriptions_manager

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
        try:
            db.execute(
                "INSERT INTO user (id, name, email, token, organization, domain_name) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (id_, name, email, token, organization, domain_name,),
            )
        except sqlite3.IntegrityError:
            return -1
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
            "INSERT INTO apps (name, user_id) "
            "VALUES (?, ?)",
            (app, user,),
        )
        db.commit()

    def delete_app_user(user, app, path=None):
        db=get_db(path)
        query = "DELETE FROM apps WHERE user_id = ? and name = ?"
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

    def get_all_cond(table, field, cond_field, cond, path=None):
        db = get_db(path)
        query = "SELECT " + field + " FROM " + table + " WHERE " + cond_field + "= ?"
        data = db.execute(query, (cond,)).fetchall()
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

    @staticmethod
    def get_app_org(user_id):
        db = get_db()
        app_org = db.execute(
            "SELECT application, organization FROM user WHERE id = ?", (user_id,)
        ).fetchone()
        return [app_org[0], app_org[1]]


    # Subscription management methods
    @staticmethod
    def create_subscription(user_id, subscription_type, endpoint_url, DB_url, query, interval, active):
        db = get_db()
        try:
            db.execute(
                "INSERT INTO subscriptions (user_id, subscription_type, endpoint_url, DB_url, query, interval, active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            )
            
            # Get the subscription_id of the newly created subscription
            subscription_id = db.execute(
                "SELECT subscription_id FROM subscriptions WHERE user_id = ? AND subscription_type = ? AND endpoint_url = ? AND DB_url = ? AND query = ? AND interval = ? AND active = ?",
                (user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            )
            
            # Update the subscriptions in the ./ES_alert_system/config.json file
            subscriptions_manager.add_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            
            
            db.commit()
        except sqlite3.IntegrityError as e:
            return str(e)
        return 'Subscription created successfully'

    @staticmethod
    def get_subscriptions(user_id):
        db = get_db()
        subscriptions = db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return subscriptions


    @staticmethod
    def get_subscription(subscription_id):
        db = get_db()
        subscription = db.execute(
            "SELECT * FROM subscriptions WHERE subscription_id = ?",
            (subscription_id,)
        ).fetchone()
        return subscription

    @staticmethod
    def update_subscription(subscription_id, **kwargs):
        db = get_db()
        fields = ', '.join(f"{key} = ?" for key in kwargs)
        values = list(kwargs.values())
        values.append(subscription_id)
        try:
            db.execute(
                f"UPDATE subscriptions SET {fields} WHERE subscription_id = ?",
                values
            )
            
            # Get the subscription_id of the newly created subscription
            subscription_id = db.execute(
                "SELECT subscription_id FROM subscriptions WHERE user_id = ? AND subscription_type = ? AND endpoint_url = ? AND DB_url = ? AND query = ? AND interval = ? AND active = ?",
                (user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            )
            
            # Update the subscriptions in the ./ES_alert_system/config.json file
            subscriptions_manager.update_subscription(subscription_id, user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            
            db.commit()
        except:
            return str(e)
        return 'Subscription updated successfully'

    @staticmethod
    def delete_subscription(subscription_id):
        db = get_db()
        try:
            db.execute(
                "DELETE FROM subscriptions WHERE subscription_id = ?",
                (subscription_id,)
            )
            
            # Get the subscription_id of the newly created subscription
            subscription_id = db.execute(
                "SELECT subscription_id FROM subscriptions WHERE user_id = ? AND subscription_type = ? AND endpoint_url = ? AND DB_url = ? AND query = ? AND interval = ? AND active = ?",
                (user_id, subscription_type, endpoint_url, DB_url, query, interval, active)
            )
            
            # Update the subscriptions in the ./ES_alert_system/config.json file
            subscriptions_manager.delete_subscription(subscription_id)
            
            db.commit()
        except:
            return str(e)
        return 'Subscription deleted successfully'
        
        
    @staticmethod
    def delete_all_subscriptions():
        db = get_db()
        db.execute(
            "DELETE FROM subscriptions"    
        )
        db.commit()