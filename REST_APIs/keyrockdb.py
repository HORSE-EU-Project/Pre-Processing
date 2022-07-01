import mysql.connector

def keyrockdb_connect():
    mydb = mysql.connector.connect(
        host="10.0.18.77",
        user="root",
        password="pass",
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
