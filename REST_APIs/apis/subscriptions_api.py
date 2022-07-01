from flask import abort, request
from flask_restx import Resource, Namespace, reqparse, fields
from marshmallow import Schema, validate
import marshmallow
import sys
import os
import json
from bson import json_util
from bson.objectid import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import user
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import oriondb
import requests
import keyrockdb


api = Namespace('subscriptions', description='Subscription related operations')

class deleteSubscriptionSchema(Schema):
    subId = marshmallow.fields.String(validate=validate.Regexp("^[a-zA-Z0-9]{24}$"), required=True)

deleteSubSchema = deleteSubscriptionSchema()

parser = reqparse.RequestParser()

parser.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')

okay_response_get = api.model('GET Subscriptions', {
    'subs': fields.List(fields.Raw)
})

okay_response_post = api.model('POST Subscriptions', {
    'message': fields.String
})

okay_response_del = api.model('DEL Subscriptions', {
    'message': fields.String
})

@api.route('')
class orionSubscriptions(Resource):
    global db 
    db = "orion"
    global col
    col = "csubs"
    @api.response(200, "OK", okay_response_get)
    @api.doc(parser=parser)
    @api.response(204, 'Either you do not owe any subscriptions or you mistyped the domain_name that your application uses for subscriptions when you registered your app.')
    @api.response(400, 'This method does not accept any parameters.')
    @api.response(403, 'Either your domain name is not registered in the DFF Web App or you need to get a fresh token.')
    @api.response(404, 'The domain name that your app uses for subscriptions is not set: you need to set it through the DFF Web App before attempting this request.')
    @api.response(500, 'While trying to connect to MongoDB, an error occurred.')
    def get(self):
        if request.args:
            abort(400, "This method does not accept any parameters.")
        token = request.headers.get('X-Auth-token')
        try:
            mydb = keyrockdb.keyrockdb_connect()
        except:
            abort(500, "While trying to connect with Keyrock DB an error occurred.")
        user_id = keyrockdb.keyrockdb_get(mydb, "user_id", "oauth_access_token", "access_token", token)
        print(user_id)
        domain = user.User.get_field("id", user_id, "user", "domain_name", path = "../../DFF_Web_App/")
        if domain==-1:
            abort(403, "Either there aren't any subscriptions created for your domain name or you need to get a fresh token.")
        elif domain==None:
            abort(404, "The domain name that your app uses for subscriptions is not set: you need to set it through the DFF Web App before attempting this request.")
        try:
            client = oriondb.mongoConnect(db)
        except:
            abort(500, 'While trying to connect to MongoDB, an error occurred.')
        subs = oriondb.getSubscriptions(client, db, col, "reference", domain, None)
        oriondb.mongoCloseConnection(client)
        if subs:
            return {"subs": json.loads(json_util.dumps(subs))}, 200
        else:
            return {"message": "Either you do not owe any subscriptions or you mistyped the domain name that your application uses for subscriptions when you registered your app."}, 204
    
    @api.doc(parser=parser)
    @api.response(200, "OK", okay_response_post)
    def post(self):
        token = request.headers.get('X-Auth-token') 
        body = request.get_json()
        header = {
            "Content-Type" : "application/json",
            "X-Auth-token" : token
        }
        r = requests.post(url="http://10.0.20.174:1027/v2/subscriptions/", headers=header, data=json.dumps(body), verify=False)
        if(r.status_code==201):
            return {"message": "Subscription created successfully."}, 200
        else:
            abort(r.status_code, r.json())
    
    parser.add_argument('subId', type=str, location = 'args', help='The ObjectId of the subscription document that you wish to delete.')
    @api.doc(parser=parser)
    @api.response(200, "OK", okay_response_del)
    @api.response(400, 'Validation error')
    @api.response(401, "Either the requested entity does not exist or you are not authorized to delete it.")
    @api.response(403, 'You are not registered in the database: you need to login through the DFF Web App first.')
    @api.response(404, 'The domain name that your app uses for subscriptions is not set: you need to set it through the DFF Web App before attempting this request.')
    @api.response(500, 'While trying to connect to MongoDB, an error occurred.')
    @api.response(502, "The deletion was unsuccessful.")
    def delete(self):
        errors = deleteSubSchema.validate(request.args)
        if errors:
            abort(400, 'Validation error')
        token = request.headers.get('X-Auth-token')
        try:
            mydb = keyrockdb.keyrockdb_connect()
        except:
            abort(500, "While trying to connect with Keyrock DB an error occurred.")
        user_id = keyrockdb.keyrockdb_get(mydb, "user_id", "oauth_access_token", "access_token", token)
        print(user_id)
        domain = user.User.get_field("id", user_id, "user", "domain_name", path = "../../DFF_Web_App/")
        if domain==-1:
            abort(403, "You are not registered in the database: you need to login through the DFF Web App first.")
        elif domain==None:
            abort(404, "The domain name that your app uses for subscriptions is not set: you need to set it through the DFF Web App before attempting this request.")
        inputSubId = request.args["subId"]
        subId = ObjectId(inputSubId)
        try:
            client = oriondb.mongoConnect(db)
        except:
            abort(500, 'While trying to connect to MongoDB, an error occurred.')
        for d in oriondb.getSubscriptions(client, db, col, "reference", domain, "_id"):
            if subId in d.values():
                result = oriondb.deleteSubscription(client, db, col, "_id", subId)
                oriondb.mongoCloseConnection(client)
                if result.acknowledged == True:
                    return {"message": "The requested entity was deleted."}, 200
                else:
                    abort(502, "The deletion was unsuccessful.")
            else:
                oriondb.mongoCloseConnection(client)
                abort(401, "Either the requested entity does not exist or you are not authorized to delete it.")
    
        
        
        
        
        
        
        
    
        