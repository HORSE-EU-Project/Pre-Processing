from flask import abort, request
from flask_restx import Namespace, Resource, reqparse, fields
import requests
import json
import sys
import os

from marshmallow import Schema, validate
import marshmallow

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import user

api = Namespace('dffData', description='Crate data related operations')

class DataPerIndexQuerySchema(Schema):
    inputType = marshmallow.fields.String(validate=validate.Regexp("^[a-zA-Z]+$"), required=True)
    entityId = marshmallow.fields.String(validate=validate.Regexp("^[a-zA-Z_0-9]+$"), required=False)
    lastN = marshmallow.fields.Integer(required=False)
    fromDate = marshmallow.fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)
    toDate = marshmallow.fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)

getDataSchema = DataPerIndexQuerySchema()

class DeletDataSchema(Schema):
    inputType = marshmallow.fields.String(validate=validate.Regexp("^[a-zA-Z]+$"), required=True)
    entityId = marshmallow.fields.String(validate=validate.Regexp("^[a-zA-Z_0-9]+$"), required=True)

deleteDataSchema = DeletDataSchema()

parserG = reqparse.RequestParser()

parserG.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')

parserD = reqparse.RequestParser()

parserD.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')
parserD.add_argument('inputType', type=str, location = 'args', help='The application (equivalent to type in DFF) that you want to delete data from, e.g. XBELLO.')
parserD.add_argument('entityId', type=str, location = 'args', help='The id of the specific entity -belonging to this specific application- whose data you want to delete.')

okay_response_post = api.model('POST data', {
    'message': fields.String
})

okay_response_del = api.model('DEL data', {
    'message': fields.String
})

def checkIfTableExists(url, header, table):
    body = "{\"stmt\":\"SHOW tables\"}"
    r = requests.post(url=url, headers=header, data=body, verify=False)
    if r.status_code != 200:
        abort(r.status_code, "An error occurred while retrieving data from the database")
    tableExists = False
    for i in r.json()["rows"]:
        if table in i:
            tableExists = True
    if not tableExists:
        abort(404, "The application you have entered does not exist.")
    return tableExists

@api.route('')
class GetTypeDataPerTimeIndex(Resource):
    parserG.add_argument('inputType', type=str, location = 'args', help='The application (equivalent to type in DFF) that you want to get data from, e.g. XBELLO.')
    parserG.add_argument('entityId', type=str, location = 'args', help='The id of the specific entity -belonging to this specific application- that you want to retrieve data from.')
    parserG.add_argument('lastN', type=int, location='args', help='The number of last data entries that you wish to retrieve.')
    parserG.add_argument('fromDate', type=str, location = 'args', help='The date after which you want to receive data for the specified application. It may be either date or datetime or datetime with timezone in the ISO-8601 format (e.g., 2022-05-31T06:57:00+0000). The default timezone is UTC.')
    parserG.add_argument('toDate', type=str, location = 'args', help='The date until which you want to receive data for the specified application. It may be either date or datetime or datetime with timezone in the ISO-8601 format (e.g., 2022-05-31T06:57:00+0000). The default timezone is UTC.')
    @api.doc(parser=parserG)
    @api.response(200, 'OK')
    @api.response(400, 'Validation error')
    @api.response(404, 'The application you have entered does not exist')
    def get(self):
        if "fromDate" in request.args and "toDate" in request.args:
            fromD = request.args["fromDate"].replace(" ", "+")
            toD = request.args["toDate"].replace(" ", "+")
        elif "fromDate" in request.args:
            toD=None
            fromD = request.args["fromDate"].replace(" ", "+")
        elif "toDate" in request.args:
            fromD=None
            toD = request.args["toDate"].replace(" ", "+")
        else:
            toD=None
            fromD=None
        if "lastN" in request.args:
            lastN = request.args["lastN"]
        else:
            lastN=None
        if "entityId" in request.args:
            entityId=request.args["entityId"]
            print(entityId)
        else:
            entityId=None
        errors = getDataSchema.validate(request.args)
        if errors:
            abort(400, 'Validation error')
        header={
            "Content-Type": "application/json"
        }
        dType = request.args["inputType"]
        table = "et" + dType.lower()
        url = "http://10.0.18.77:4200/_sql"
        checkIfTableExists(url, header, table)
        if fromD==None and toD==None:
            if lastN==None and entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " ORDER BY time_index DESC;\"}"
            elif entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
            elif lastN==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE entity_id = \'" + entityId + "\' ORDER BY time_index DESC;\"}"
            else:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE entity_id = \'" + entityId + "\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
        elif fromD==None:
            if lastN==None and entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index < \'"+ toD +"\' ORDER BY time_index DESC;\"}"
            elif entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index < \'"+ toD +"\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}" 
            elif lastN==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index < \'"+ toD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC;\"}"
            else:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index < \'"+ toD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
        elif toD==None:
            if lastN==None and entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' ORDER BY time_index DESC;\"}"
            elif entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
            elif lastN==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC;\"}"
            else:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
        else:
            if lastN==None and entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and time_index < \'"+ toD +"\' ORDER BY time_index DESC;\"}"
            elif entityId==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and time_index < \'"+ toD +"\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
            elif lastN==None:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and time_index < \'"+ toD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC;\"}"
            else:
                body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and time_index < \'"+ toD +"\' and entity_id = \'" + entityId + "\' ORDER BY time_index DESC LIMIT " + lastN + ";\"}"
        r = requests.post(url=url, headers=header, data=body, verify=False)
        if r.status_code != 200:
            abort(r.status_code, "An error occurred while retrieving data from the database")
        data = r.json()
        entities = []
        for row in data["rows"]:
            new_data_dict = {}
            new_data_dict["attributes"] = []
            for i in range(0, len(row)):
                column = data["cols"][i]
                if column != "fiware_servicepath" and column != "__original_ngsi_entity__":
                    if i<5:
                        new_data_dict[data["cols"][i]] = row[i]
                    else:
                        (new_data_dict["attributes"]).append({"attrName": data["cols"][i], "value": row[i]})
            entities.append(new_data_dict)
        return entities, 200

    @api.doc(parser=parserD)
    @api.response(200, 'OK', okay_response_post)
    def post(self):
        token = request.headers.get('X-Auth-token') 
        body = request.get_json()
        header = {
            "Content-Type" : "application/json",
            "X-Auth-token" : token
        }
        name=user.User.get_field("token", token, "user", "name", "../../DFF_Web_App/")
        if name==-1:
            abort(500, "Please, get a fresh token!")
        dffMetadata = {"type": "user", "value": name}
        for i in range(0, len(body["entities"])):
            body["entities"][i]["dfm_metadata"] = dffMetadata
        print("hello")
        r = requests.post(url="http://10.0.20.174:1027/v2/op/update", headers=header, data=json.dumps(body), verify=False)
        if(r.status_code==204):
            return {"message": "Data posted successfully."}, 200
        else:
            abort(r.status_code, r.json())
    
    @api.doc(parser=parserD)
    @api.response(200, 'OK', okay_response_del)
    @api.response(400, 'Validation error')
    @api.response(404, 'The application you have entered does not exist')
    @api.response(401, 'You are not allowed to delete data from an application you do not owe.')
    def delete(self):
        token = request.headers.get('X-Auth-token') 
        errors = deleteDataSchema.validate(request.args)
        if errors:
            abort(400, 'Validation error')
        header={
            "Content-Type": "application/json"
        }
        dType = request.args["inputType"]
        app=user.User.get_field("token", token, "user", "application", "../../DFF_Web_App/")
        entityId = request.args["entityId"]
        table = "et" + dType.lower()
        url = "http://10.0.18.77:4200/_sql"
        checkIfTableExists(url, header, table)
        if app == dType:
            body = "{\"stmt\":\"DELETE FROM doc." + table + " WHERE entity_id = \'" + entityId + "\';\"}"
            r = requests.delete(url=url, headers=header, data=body, verify=False)
            if r.status_code != 200:
                abort(r.status_code, "An error occurred while retrieving data from the database")
            else:
                return {"message": "No. of row(s) deleted: " + str(r.json()["rowcount"])}, 200
        else:
            abort(401, "You are not allowed to delete data from an application you do not owe.")