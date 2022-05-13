from pickle import FALSE
from flask import Flask, abort, request
from flask_restful import Resource, Api
import requests
import socket
from marshmallow import Schema, fields, validate

class DataPerIndexQuerySchema(Schema):
    inputType = fields.String(validate=validate.Regexp("^[a-zA-Z]+$"), required=True)
    fromDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)
    toDate = fields.String(validate=validate.Regexp("^\"*\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d(\.\d+)?(([ -]\d\d:\d\d)|Z)?)*\"*$"), required=False)

app = Flask(__name__)
api = Api(app)
getDataSchema = DataPerIndexQuerySchema()

class GetTypeDataPerTimeIndex(Resource):
    def get(self):
        if "fromDate" in request.args and "toDate" in request.args:
            fromD = request.args["fromDate"]
            toD = request.args["toDate"]
            request.args.get("fromDate").encode('UTF-8')
            request.args.get("toDate").encode('UTF-8')
        else:
            fromD=None
            toD=None
        errors = getDataSchema.validate(request.args)
        if errors:
            abort(400, str(errors))
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
            return {"message": "The type your are requesting data for does not exist."}, 400
        if fromD==None and toD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + " ORDER BY time_index;\"}"
        elif fromD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + "WHERE time_index<" + toD + "::TIMESTAMP ORDER BY time_index;\"}"
        elif toD==None:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + "WHERE time_index>" + fromD + "::TIMESTAMP ORDER BY time_index;\"}"
        else:
            body = "{\"stmt\":\"SELECT * FROM doc." + table + "WHERE time_index>" + fromD + "::TIMESTAMP AND time_index<" + toD + "::TIMESTAMP ORDER BY time_index;\"}"
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

api.add_resource(GetTypeDataPerTimeIndex, '/getTypeData')

if __name__ == '__main__':
    ipV4IP = socket.gethostbyname(socket.gethostname())
    app.run(host=ipV4IP, port=5003, debug=True)