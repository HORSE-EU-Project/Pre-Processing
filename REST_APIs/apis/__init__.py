from flask_restx import Api

from .crate_data_api import api as ns1
from .subscriptions_api import api as ns2
from .login_api import api as ns3

api = Api(
    title='DFF REST APIs',
    version='1.0',
    description='These are the DFF REST APIs to login and manage data & subscriptions.'
)

api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)