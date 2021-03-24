import requests
import os

from modelos import Usuario
from autentificar import get_access_token


class Api(object):
    # Obtener perfil de Twitter de un usuario.
    # Argumento 'username' debe ser tipo String.
    @staticmethod
    def get_usuario_segun_nombre_usuario(username) -> dict:
        usuario = {}
        access_token = get_access_token()

        # Más información sobre los datos recibidos en
        # https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by-username-username
        respuesta = requests.get('{}/2/users/by/username/{}?user.fields=created_at,description,entities,id,location,name,profile_image_url,public_metrics,url,username'
                                 .format(os.getenv('API_TWITTER_URL'), username),
                                 headers={'Authorization': 'Bearer {}'.format(access_token)})
        # Ejemplo del campo 'data'
        # {
        #     'id': '197103453',
        #     'username': 'sergidelmoral',
        #     'name': 'Sergi del Moral',
        #     'public_metrics': {
        #         'followers_count': 6850, 'following_count': 1060, 'tweet_count': 17391, 'listed_count': 218
        #         }
        # }
        data = HttpResponse.get_campo_data(respuesta)
        usuario = Usuario(data['id'], data['username'], data['name'],
                          data['public_metrics']['followers_count'], data['public_metrics']['following_count'])
        return usuario.__dict__

    # Obtener perfiles de Twitter de una lista de máximo 100 usuarios.
    # Argumento 'usernames' debe ser una lista de tipo `str`.
    @staticmethod
    def get_usuarios_segun_nombre_usuario(nombre_usuarios) -> list:
        usuarios = []
        nombre_usuarios_agrupados = ','.join(nombre_usuarios)
        access_token = get_access_token()

        # Más información sobre los datos recibidos en
        # https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-by-username-username
        respuesta = requests.get('{}/2/users/by?usernames={}&user.fields=created_at,description,entities,id,location,name,profile_image_url,public_metrics,url,username'
                                 .format(os.getenv('API_TWITTER_URL'), nombre_usuarios_agrupados),
                                 headers={'Authorization': 'Bearer {}'.format(access_token)})

        # Ejemplo de los datos
        # [{
        #     'id': '197103453',
        #     'username': 'sergidelmoral',
        #     'name': 'Sergi del Moral',
        #     'public_metrics': {
        #         'followers_count': 6850, 'following_count': 1060, 'tweet_count': 17391, 'listed_count': 218
        #         }
        # }]
        data = HttpResponse.get_campo_data(respuesta)

        for usuario in data:
            usuario = Usuario(usuario['id'], usuario['username'], usuario['name'],
                              usuario['public_metrics']['followers_count'], usuario['public_metrics']['following_count'])
            usuarios.append(usuario.__dict__)

        return usuarios

    @staticmethod
    def get_historial_usuario(id_usuario) -> list:
        # Obtener historial de interacciones que ha hecho el usuario
        # en Twitter. Las interacciones pueden ser tweet, retweet,
        # respuesta o tweet citado (tweet con comentario).
        # Argumento 'id_usuario' debe ser tipo 'string'.

        historial = []  # Se encuentran todas las interacciones del usuario
        numero_total_interacciones = 0  # Totola de interacciones recabadas.
        numero_interacciones_por_solicitud = 0
        ACCESS_TOKEN = get_access_token()
        MODO_ARRANQUE = os.getenv('MODO_ARRANQUE')

        # Hacemos la primera solicitud de datos (Twitter pone un límite de
        # 100 ítems por cada solicitud). Si estamos en modo prueba (modo debug),
        # solo solicitamos las 30 últimas interacciones del usuario.
        # Más información en https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
        respuesta = requests.get('{}/2/users/{}/tweets?max_results={}&tweet.fields=text,author_id,entities,in_reply_to_user_id,referenced_tweets,created_at,lang,public_metrics&media.fields=type,public_metrics'
                                 .format(os.getenv('API_TWITTER_URL'), id_usuario, 100 if MODO_ARRANQUE != 'debug' else 20),
                                 headers={'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)})

        print('historial userid={} con respuesta={}'.format(id_usuario, respuesta))

        historial = HttpResponse.get_campo_data(respuesta)

        numero_total_interacciones += HttpResponse.get_campo_meta(respuesta)[
            'result_count']
        token_siguiente_solicitud = HttpResponse.get_campo_meta(respuesta)[
            'next_token']

        # Hacemos múltiples solicitudes para recabar los últimos
        # 500 ítems del historial del usuario.
        # En mode DEBUG, solo cogemos pocos datos
        # IMPORTANTE: Twitter no deja recabar más de 100 resultados por solicitud
        while (MODO_ARRANQUE != 'debug' and numero_total_interacciones < 400):
            # Código para hacer solicitudes de los siguiente datos del historial del usuario

            respuesta = requests.get('{}/2/users/{}/tweets?max_results=100&pagination_token={}&tweet.fields=text,author_id,entities,in_reply_to_user_id,referenced_tweets,created_at,lang,public_metrics&media.fields=type,public_metrics'
                                     .format(os.getenv('API_TWITTER_URL'), id_usuario, token_siguiente_solicitud),
                                     headers={'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)})

            interacciones = HttpResponse.get_campo_data(respuesta)

            # Unir lista de nuevas interacciones a la lista de historial
            historial.extend(interacciones)
            # historial = [*historial, *interacciones]
            # historial= list(chain(historial, interacciones))

            numero_interacciones_por_solicitud = HttpResponse.get_campo_meta(respuesta)[
                'result_count']
            numero_total_interacciones += numero_interacciones_por_solicitud
            token_siguiente_solicitud = HttpResponse.get_campo_meta(respuesta)[
                'next_token']

            print('numero_total_interacciones=', numero_total_interacciones)

            # Si en la solicitud obtenemos menos de 10 resultados, quiere decir que
            # no hay más historial del usuario. Por tanto, paramos las solicitudes.
            # Sino, continuamos haciendo solicitudes.
            if numero_interacciones_por_solicitud < 100:
                break
            else:
                continue

        print('Obtenidos {} interacciones'.format(
            numero_total_interacciones))
        # Ejemplo del historal
        # [
        #     {
        #         "author_id": "197103453",
        #         "referenced_tweets": [
        #             {
        #                 "type": "replied_to",
        #                 "id": "1342040611722035200"
        #             }
        #         ],
        #         "entities": {
        #             "mentions": [
        #                 {
        #                     "start": 0,
        #                     "end": 13,
        #                     "username": "EmmaLpezArs1"
        #                 }
        #             ]
        #         },
        #         "id": "1342046214322335744",
        #         "in_reply_to_user_id": "1336763144035819520",
        #         "text": "@EmmaLpezArs1 Emma, el meu domini de les emoticones és limitat, :). No entenc el teu missatge, però això no treu que em faci il·lusió."
        #     }
        # ],
        return historial


class HttpResponse(object):
    @staticmethod
    def check_error_respuesta_http(respuesta):
        if respuesta.status_code != 200:
            raise Exception(
                "Request returned an error {} {}".format(
                    respuesta.status_code, respuesta.text
                )
            )

    # Argumento 'respuesta_http' debe ser la respuesta obtenida
    # cuando se hace un solicitud o request HTTP con la libraría 'requests'.
    # No debe estar formateado JSON ni dict.
    @staticmethod
    def get_campo_data(respuesta_http) -> dict:
        HttpResponse.check_error_respuesta_http(respuesta_http)
        # Convertir a formato JSON y obtener campo 'data'.
        data = respuesta_http.json()['data']
        return data

    # Argumento 'respuesta_http' debe ser la respuesta obtenida
    # cuando se hace un solicitud o request HTTP con la libraría 'requests'.
    # No debe estar formateado JSON ni dict.
    @staticmethod
    def get_campo_meta(respuesta_http) -> dict:
        HttpResponse.check_error_respuesta_http(respuesta_http)
        # Convertir a formato JSON y obtener campo 'meta'.
        # Un ejemplo de los datos que contiene 'meta' está en esta documentación https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
        meta = respuesta_http.json()['meta']

        return meta
