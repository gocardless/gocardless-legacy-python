from .client import Client

environment = 'production'
global_client = None

def set_details(details):
    """Set the global account details to use for requests

    Should be a dictionary with the following keys
    - app_id 
    - app_secret
    - token 
    - merchant_id
    """
    global global_client
    global_client = Client(**details)

