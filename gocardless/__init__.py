from .client import Client

environment = 'production'
client = None

def set_details(details):
    client = Client(details)

