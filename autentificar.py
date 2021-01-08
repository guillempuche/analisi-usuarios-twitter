from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import os


access_token = None

def get_access_token():
    global access_token
    
    if type(access_token) is str:
        return access_token
    else:
        # Variables constantes
        api_twitter_url = os.getenv('API_TWITTER_URL')
        consumer_key = os.getenv('CONSUMER_KEY')
        consumer_secret = os.getenv('CONSUMER_SECRET')

        # Autentificar a la API de Twitter. Nos va a dar la clave
        # 'access_token' para sacar datos a la API
        respuesta = requests.post(api_twitter_url+'/oauth2/token',
                                  data={'grant_type': 'client_credentials'},
                                  auth=HTTPBasicAuth(consumer_key, consumer_secret))
        access_token = respuesta.json()['access_token']
        return access_token
