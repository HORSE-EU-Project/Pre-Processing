from flask import abort, request
from flask_restx import Namespace, Resource, reqparse
import requests
import json
import sys
import os

from marshmallow import Schema, fields, validate

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
import user

api = Namespace('dffData', description='Crate data related operations')

class DataPerIndexQuerySchema(Schema):
    inputType = fields.String(validate=validate.Regexp("^[a-zA-Z]+$"), required=True)
    fromDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)
    toDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)

getDataSchema = DataPerIndexQuerySchema()

parserG = reqparse.RequestParser()

parserG.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')

parserD = reqparse.RequestParser()

parserD.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')

okay_response_post = api.model('POST Subscriptions', {
    'message': fields.String
})

@api.route('/')
class GetTypeDataPerTimeIndex(Resource):
    parserG.add_argument('inputType', type=str, location = 'args', help='The application (equivalent to type in DFF) that you want to get data from, e.g. XBELLO.')
    parserG.add_argument('fromDate', type=str, location = 'args', help='The date after which you want to receive data for the specified application. It may be either date or datetime or datetime with timezone in the ISO-8601 format (e.g., 2022-05-31T06:57:00+0000). The default timezone is UTC.')
    parserG.add_argument('toDate', type=str, location = 'args', help='The date until which you want to receive data for the specified application. It may be either date or datetime or datetime with timezone in the ISO-8601 format (e.g., 2022-05-31T06:57:00+0000). The default timezone is UTC.')
    @api.doc(parser=parserG)
    @api.response(200, 'OK')
    @api.response(400, 'Validation error')
    @api.response(404, 'The application your are requesting data from does not exist.')
    def get(self):
        print(request.headers.get('X-Auth-token'))
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
        errors = getDataSchema.validate(request.args)
        if errors:
            abort(400, 'Validation error')
        header={
            "Content-Type": "application/json"
        }
        dType = request.args["inputType"]
        table = "et" + dType.lower()
        url = "http://10.0.18.77:4200/_sql"
        body = "{\"stmt\":\"SHOW tables\"}"
        r = requests.post(url=url, headers=header, data=body, verify=False)
        if r.status_code != 200:
            return {"message": "An error occurred while retrieving data from the database"}, r.status_code
        tableExists = False
        for i in r.json()["rows"]:
            if table in i:
                tableExists = True
        if not tableExists:
            abort(404, "The application your are requesting data from does not exist.")
        if fromD==None and toD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + " ORDER BY time_index;\"}"
        elif fromD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index < \'"+ toD +"\' ORDER BY time_index;\"}"
        elif toD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' ORDER BY time_index;\"}"
        else:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + " WHERE time_index > \'"+ fromD +"\' and time_index < \'"+ toD +"\' ORDER BY time_index;\"}"
        r = requests.post(url=url, headers=header, data=body, verify=False)
        if r.status_code != 200:
            return {"message": "An error occurred while retrieving data from the database"}, r.status_code
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
            abort(500, "Internal Server Error.")
        dffMetadata = {"type": "user", "value": name}
        for i in range(0, len(body["entities"])):
            body["entities"][i]["dfm_metadata"] = dffMetadata
        r = requests.post(url="http://jenkins.8bellsresearch.com:1027/v2/op/update", headers=header, data=json.dumps(body), verify=False)
        if(r.status_code==204):
            return {"message": "Data posted successfully."}, 200
        else:
            abort(r.status_code, r.json())
        