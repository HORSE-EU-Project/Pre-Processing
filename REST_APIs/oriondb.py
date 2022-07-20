from pymongo import MongoClient
import os 

DB_URL = "mongodb://cloud-20-nic.8bellsresearch.com:27017/"
MONGO_DB_PASS=os.getenv("MONGO_DB_PASS")

def mongoConnect(database):
    client = MongoClient(DB_URL, username='user', password=MONGO_DB_PASS, authSource=database, directConnection=True)
    return client
  
def mongoCloseConnection(client):
    client.close()
    return

def getSubscriptions(client, database, collection, filter_field, filter, projection):
    mydb = client[database]
    mycol = mydb[collection]
    subs = []
    if projection:
        for r in mycol.find({filter_field: { '$regex': filter } }, {projection: 1}):
            subs.append(r)
    else:
        for r in mycol.find({filter_field: { '$regex': filter } }):
            subs.append(r)
    return subs

def deleteSubscription(client, database, collection, filter, data):
    mydb = client[database]
    mycol = mydb[collection]
    result = mycol.delete_one({filter: data})
    return result

