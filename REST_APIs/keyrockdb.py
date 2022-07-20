import mysql.connector
import os

MYSQL_PASS = os.environ.get("MYSQL_PASS")

def keyrockdb_connect():
    mydb = mysql.connector.connect(
        host="cloud-20-nic.8bellsresearch.com",
        user="root",
        password=MYSQL_PASS,
        database="idm"
    )
    return mydb

def keyrockdb_get(mydb, field, table, cond_field, cond):
    mycursor = mydb.cursor()
    query="SELECT " + field + " FROM " + table + " WHERE " + cond_field + "=%s"
    val=(cond, )
    mycursor.execute(query, val)
    myresult = mycursor.fetchone()
    if myresult:
        myresult=myresult[0]
    else:
        return -1
    return myresult
