from flask import abort, request
from flask_restx import Resource, Namespace
from marshmallow import Schema, fields, validate
import sys
import os
import json
from bson import json_util
from bson.objectid import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import user
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import oriondb

api = Namespace('subscriptions', description='Subscription related operations')

class deleteSubscriptionSchema(Schema):
    subId = fields.String(validate=validate.Regexp("^[a-zA-Z0-9]{24}$"), required=True)

deleteSubSchema = deleteSubscriptionSchema()

@api.route('/')
class orionSubscriptions(Resource):
    global db 
    db = "orion"
    global col
    col = "csubs"
    def get(self):
        if request.args:
            abort(400, "This method does not accept any parameters.")
        token = request.headers.get('X-Auth-token')
        domain = user.User.get_field("token", token, "user", "domain_name", path = "../../DFF_Web_App")
        client = oriondb.mongoConnect(db)
        subs = oriondb.getSubscriptions(client, db, col, domain, None)
        oriondb.mongoCloseConnection(client)
        if subs:
            return {"subs": json.loads(json_util.dumps(subs))}, 200
        else:
            return {"message": "You do not have any subscriptions."}, 204

    def delete(self):
        errors = deleteSubSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
        token = request.headers.get('X-Auth-token')
        domain = user.User.get_field("token", token, "user", "domain_name", path = "../../DFF_Web_App")
        inputSubId = request.args["subId"]
        subId = ObjectId(inputSubId)
        client = oriondb.mongoConnect(db)
        for d in oriondb.getSubscriptions(client, db, col, domain, "_id"):
            if subId in d.values():
                result = oriondb.deleteSubscription(client, db, col, "_id", subId)
                oriondb.mongoCloseConnection(client)
                if result.acknowledged == True:
                    return {"message": "The requested entity was deleted."}, 200
                else:
                    abort(500, "The deletion was not performed.")
            else:
                oriondb.mongoCloseConnection(client)
                abort(401, "Either the requested entity does not exist or you are not authorized to delete it.")