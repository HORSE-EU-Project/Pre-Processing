from flask import abort, request
from flask_restx import Namespace, Resource, reqparse
import requests

from marshmallow import Schema, fields, validate

api = Namespace('dffData', description='Crate data related operations')

class DataPerIndexQuerySchema(Schema):
    inputType = fields.String(validate=validate.Regexp("^[a-zA-Z]+$"), required=True)
    fromDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)
    toDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)

getDataSchema = DataPerIndexQuerySchema()

parser = reqparse.RequestParser()

parser.add_argument('X-Auth-token', location='headers', help='The token that you have acquired either from the DFF Web App or the DFF login api.')

@api.route('/getTypeData')
class GetTypeDataPerTimeIndex(Resource):
    @api.doc(parser=parser)
    @api.response(200, 'OK')
    @api.response(400, 'Validation error')
    @api.response(404, 'The type your are requesting data for does not exist.')
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
            abort(404, "The type your are requesting data for does not exist.")
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