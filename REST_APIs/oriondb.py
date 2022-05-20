from pymongo import MongoClient
import os
import jsonify

# USER = os.getenv("USER")
# PASS = os.getenv("PASS")

def mongoConnect(database):
    client = MongoClient("mongodb://10.0.18.77:27017/"+database, directConnection=True)
    return client
  
def mongoCloseConnection(client):
    client.close()
    return

def getSubscriptions(client, database, collection, filter, projection):
    mydb = client[database]
    mycol = mydb[collection]
    subs = []
    if projection:
        for r in mycol.find({"reference": { '$regex': filter } }, {projection: 1}):
            subs.append(r)
    else:
        for r in mycol.find({"reference": { '$regex': filter } }):
            subs.append(r)
    return subs

def deleteSubscription(client, database, collection, filter, data):
    mydb = client[database]
    mycol = mydb[collection]
    result = mycol.delete_one({filter: data})
    return result

