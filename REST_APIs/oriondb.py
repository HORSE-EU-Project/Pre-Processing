from pymongo import MongoClient

# USER = os.getenv("USER")
# PASS = os.getenv("PASS")
DB_URL = "mongodb://10.0.18.77:27017/"

def mongoConnect(database):
    client = MongoClient(DB_URL+database, directConnection=True)
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

