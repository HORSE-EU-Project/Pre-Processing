from flask_restx import Api

from .crate_data_api import api as ns1
from .subscriptions_api import api as ns2

api = Api(
    title='DFF REST API',
    version='1.0',
    description='These are the DFF REST APIs to manage data and subscriptions.'
)

api.add_namespace(ns1)
api.add_namespace(ns2)