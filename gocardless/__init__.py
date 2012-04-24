from .client import Client

#import as clientlib so that we don't shadow with the client variable
import client as clientlib

environment = 'production'
client = None

def set_details(details):
    """Set the global account details to use for requests

    Should be a dictionary with the following keys
    - app_id 
    - app_secret
    - token 
    - merchant_id
    """
    global client
    client = Client(details["app_id"],
            details["app_secret"],
            access_token=details["token"],
            merchant_id=details["merchant_id"])

