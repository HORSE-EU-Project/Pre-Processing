from flask_restx import Api

from .crate_data_api import api as ns1
from .subscriptions_api import api as ns2

api = Api(
    title='DFF REST API',
    version='0.3',
    description='This is the DFF API.',
    base_url='/apis'
)

api.add_namespace(ns1)
api.add_namespace(ns2)