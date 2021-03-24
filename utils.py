import json
import time
from os import path
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from itertools import chain


from api_twitter import Api
from modelos import UsuarioInteraccionado, Interaccion

class Archivo(object):
    # Argumento 'tipo_de_datos' tiene que explicar qué tipo de datos se guardan
    # Argumento 'datos_dict' tiene que ser tipo 'dict' (dictionary)
    @staticmethod
    def guardar_a_archivo_json(nombre_archivo, datos_dict):
        with open('./base_de_datos/{}.json'
                  .format(nombre_archivo), 'w') as archivo:
            json.dump(datos_dict, archivo)

    @staticmethod
    def leer_archivo_json(nombre_archivo) -> dict:
        # Obtener archivo que contenga JSON y convertirlo a formato dict.
        # Argumento 'nombre_archivo' es necesario y el archivo para leer
        # debe estar en la carpeta 'base_de_datos'. La nombre no debe contener
        # no el tipo de formato, es decir, no debe contener '.json'.

        with open('./base_de_datos/{}.json'
                  .format(nombre_archivo), 'r') as archivo:
            datos_json = archivo.read()
            datos = json.loads(datos_json)

        return datos


class Tiempo(object):
    def __new__(_):
        tiempo = time.localtime()
        return '{año}-{mes}-{dia} {hora}.{min}.{seg}'.format(año=tiempo.tm_year, mes=tiempo.tm_mon,
                                                             dia=tiempo.tm_mday, hora=tiempo.tm_hour,
                                                             min=tiempo.tm_min, seg=tiempo.tm_sec)


class RecolectarUsuarios(object):
    # Buscar usuario según campo i el valor del campo
    @staticmethod
    def buscar_usuario_con_posicion(lista_usuarios, campo, valor) -> dict or None:

        if campo != 'nombre_usuario' and campo != 'id':
            raise Exception('Argumento campo incorrecto')

        if len(lista_usuarios) == 0:
            print(Exception('Argumento "usuarios" debe contener algun usuario'))
            return None

        # Más información del filtro en https://stackoverflow.com/a/4391722
        posicion = next((posicion for (posicion, usuario) in enumerate(lista_usuarios)
                         if usuario[campo] == valor),
                        None)

        if posicion == None:
            return None
        else:
            return {
                'posicion': posicion,
                'usuario':  lista_usuarios[posicion]
            }

    # Buscar listado de usuarios según campo i su correspondiente valor por cada usuario
    # Argumento 'campo' puede ser 'nombre_usuario' o 'id' y su argumento
    # 'valor' correspondiente.
    @staticmethod
    def buscar_usuarios_con_posiciones(usuarios, campo, valores) -> dict or None:
        usuarios_encontrados = []

        if campo != 'nombre_usuario' or campo != 'id':
            raise Exception('Argumento campo "{}" incorrecto'.format(campo))
        if len(usuarios) == 0:
            raise Exception('Argumento "usuarios" debe contener algun usuario')

        for valor in valores:
            existe_usuario = RecolectarUsuarios.buscar_usuario_con_posicion(
                usuarios, campo, valor)
            if existe_usuario == None:
                return None
            else:
                usuarios_encontrados.append({
                    'posicion': existe_usuario['posicion'],
                    'usuario':  existe_usuario['usuario']
                })

        return usuarios_encontrados

    # Recolectar usuarios y interacciones usuarios y sus interacciones en la base de datos, sino
    # existen ahí, recolectar información en la API de Twitter.
    # Argumento 'campo' solo puede ser 'nombre_usuario'
    # 'valor' correspondiente.
    @staticmethod
    def buscar_usuarios_y_interacciones_no_existentes(lista_referencia_usuarios=[], campo='', valores=[]) -> list:
        usuarios_nuevos = []

        if (type(valores) is not list or len(valores) == 0 or campo != 'nombre_usuario'):
            raise ValueError(
                'Argumento campo o valores incorrectos')

        # Si existe ningún usuario en la lista, buscarlos en la lista local.
        # Sino ir directamente a buscar usuarios a la API
        if len(lista_referencia_usuarios) > 0:
            # Comprobar qué usuarios ya existen en la lista de referencia
            for valor in valores:
                existe_usuario = RecolectarUsuarios.buscar_usuario_con_posicion(
                    lista_referencia_usuarios, campo, valor)

                if existe_usuario == None:
                    usuarios_nuevos.append(valor)
        else:
            usuarios_nuevos = valores

        if len(usuarios_nuevos) == 0:
            print(
                'Los usuarios que quieres buscar {} ya existen en la lista.'.format(valores))
            return []

        # Buscar usuarios que no estan usuario, recolectarlo en la API de Twitter.
        # Ahora esta parte está pensada para que los elementos sean los
        # nombre de usuarios (usernames).
        if len(usuarios_nuevos) > 0:
            usuarios_nuevos = Api.get_usuarios_segun_nombre_usuario(
                usuarios_nuevos)

        # Debemos añadir las interacciones que ha tenido cada usuario
        # de la API de Twitter.
        for posicion, usuario in enumerate(usuarios_nuevos):
            historial_usuario = Api.get_historial_usuario(usuario['id'])

            interacciones_filtradas = Filtro.categorizar_interacciones(
                historial_usuario)

            # Añadir interacciones al usuario.
            usuarios_nuevos[posicion][
                'usuarios_interaccionados'] = interacciones_filtradas['usuarios_interaccionados']
            usuarios_nuevos[posicion][
                'tweets_sin_interacciones'] = interacciones_filtradas['tweets_sin_interacciones']

        return usuarios_nuevos

    @staticmethod
    def buscar_usuarios_con_interacciones_y_guardar_en_archivos(lista_ususarios_a_buscar) -> None:
        ##### IMPORTANTE: si el programa se inicia por primera vez,
        ##### debemos crear el fichero donde se guardará la información
        ##### de los usuarios.
        if path.exists('./base_de_datos/usuarios.json') == False:
            Archivo.guardar_a_archivo_json('usuarios', [])

        if (type(lista_ususarios_a_buscar) is not list or len(lista_ususarios_a_buscar) == 0):
            raise ValueError('Argumento incorrecto')
        
        usuarios_base_datos = Archivo.leer_archivo_json(
        'usuarios')

        ##### IMPORTANTE: si no se tiene ningún usuario a la base de datos, antes
        ##### añadiremos el primer usuario
        usuarios_nuevos = RecolectarUsuarios.buscar_usuarios_y_interacciones_no_existentes(
            usuarios_base_datos, 'nombre_usuario', lista_ususarios_a_buscar)

        if len(usuarios_nuevos) > 0:
            # Añadir los usuarios nuevos a en la base de datos.
            usuarios_base_datos = list(chain(usuarios_base_datos, usuarios_nuevos))
            Archivo.guardar_a_archivo_json('usuarios', usuarios_base_datos)

        #### Por cada usuario, analizaremos sus interacciones y guardaremos los archivos
        for usuario_a_buscar in lista_ususarios_a_buscar:
            ##### Obtener perfiles de usuarios analizados
            filas = []
            for usuario in usuarios_base_datos:
                filas.append([
                    usuario['id'],
                    usuario['nombre_usuario'],
                    usuario['nombre'],
                    usuario['numero_seguidores'],
                    usuario['numero_seguidos'],
                    'https://twitter.com/'+usuario['nombre_usuario']
                ])
            Tabla.crear_tabla(tipo='perfiles-usuarios',
                            titulo_archivo='./base_de_datos/perfiles-usuarios-analizados',
                            columnas=['id_twitter', 'nombre_usuario', 'nombre',
                                        'numero_seguidores', 'numero_seguidos', 'url_perfil'],
                            filas=filas)

            usuario_encontrado = RecolectarUsuarios.buscar_usuario_con_posicion(usuarios_base_datos, 'nombre_usuario', usuario_a_buscar)
            if usuario_encontrado is None:
                raise ValueError('Usuario {} no encontrado en la base de datos'.format(usuario_a_buscar))

            posicion_encontado = usuario_encontrado['posicion']
            lista_usuarios_interaccionados = Filtro.lista_usuarios_interaccionados(
                usuarios_base_datos[posicion_encontado]['usuarios_interaccionados'])
            Archivo.guardar_a_archivo_json(
                'total_interacciones_usuario_{}'.format(usuario_a_buscar), lista_usuarios_interaccionados)

            total_interacciones = Archivo.leer_archivo_json(
                'total_interacciones_usuario_{}'.format(usuario_a_buscar))
            filas = []
            for interacciones in total_interacciones:
                filas.append([
                    interacciones['nombre_usuario'],
                    interacciones['total_interacciones'],
                    interacciones['total_tweets'],
                    interacciones['total_retweets'],
                    interacciones['total_respuestas'],
                    interacciones['total_citas']
                ])
            Tabla.crear_tabla(tipo='interacciones-de-usuarioX',
                            titulo_archivo='./base_de_datos/interacciones_usuario_{}'.format(usuario_a_buscar),
                            columnas=['nombre_usuario', 'total_interacciones', 'total_tweets',
                                        'total_retweets', 'total_respuestas', 'total_citas'],
                            filas=filas,
                            usuario_origen=usuario_a_buscar)

    

# Obtener interacciones según 2 clasificaciones:
# - interacciones de usuarios mencionados
# - interacciones sin usuarios mencionados
# IMPORTANTE: las interacciones pueden ser tweet,
# retweet, respuesta o cita a un tweet.
class Filtro(object):
    @staticmethod
    def categorizar_interacciones(historial_interacciones_twitter) -> dict:
        Archivo.guardar_a_archivo_json(
            'historial-interacciones', historial_interacciones_twitter)

        usuarios_interaccionados = []
        tweets_sin_interacciones = []
        interaccion = {}

        # print('total interacciones = ', historial_interacciones_twitter.__len__)

        # Analizar cada interacción
        for i in historial_interacciones_twitter:
            # # for posicion, i in enumerate(historial_interacciones_twitter):
            # PASO 1: averiguar tipo de interacción y guardar la información.
            id_interaccion = i['id']
            texto_interaccion = i['text']
            interaccion_creada_en = i['created_at']
            idioma_interaccion = i['lang']

            # El campo 'referenced_tweets' nos dice que el usuario ha interaccionado con
            # otro usuario. Puede contenter unos de estos 3 tipos valores:
            # 'replied_to', 'retweeted' o 'quoted'. Más información en:
            # https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet
            if 'referenced_tweets' in i:
                # Mayoritariamente todos los tweets solo tiene una sola
                # referencia en la lista 'referenced_tweets'.
                referenced_tweet = i['referenced_tweets'][0]
                tipo = referenced_tweet['type']

                interaccion = Interaccion(id_interaccion,
                                          tipo,
                                          interaccion_creada_en,
                                          idioma_interaccion,
                                          texto_interaccion).__dict__
            else:
                # No es una referencia a otro tweet, sino que es
                # un tweet del propio usuario
                interaccion = Interaccion(id_interaccion,
                                          'tweet',
                                          interaccion_creada_en,
                                          idioma_interaccion,
                                          texto_interaccion).__dict__

            # PASO 2: averiguar usuario con quien se ha interaccionado

            # Extraer usuarios mencionados en la interaccicón
            if ('entities' in i) and ('mentions' in i['entities']):
                for mention in i['entities']['mentions']:
                    if 'username' in mention:
                        existe_usuario = None

                        # Saltar este pase durante el iniciio del for loop.
                        if len(usuarios_interaccionados) > 0:
                            existe_usuario = RecolectarUsuarios.buscar_usuario_con_posicion(
                                usuarios_interaccionados, 'nombre_usuario', mention['username'])

                        # Si no existe el usuario, creamos uno de nuevo
                        if existe_usuario == None:
                            nuevo_usuario_interaccionado = UsuarioInteraccionado(
                                mention['username']).__dict__
                            nuevo_usuario_interaccionado['interacciones'].append(
                                interaccion)

                            # Añadir el nuevo usuario mencionado a la lista.
                            usuarios_interaccionados.append(
                                nuevo_usuario_interaccionado)
                        # Si existe, añadimos las interacciones.
                        else:
                            posicion = existe_usuario['posicion']
                            usuarios_interaccionados[posicion]['interacciones'].append(
                                interaccion)

            else:
                # Si no hay usuarios mencionados, guardar tweets sin menciones
                tweets_sin_interacciones.append(interaccion)

        return {
            'usuarios_interaccionados': usuarios_interaccionados,
            'tweets_sin_interacciones': tweets_sin_interacciones
        }

    @staticmethod
    # Obtener lista de usuarios con número total de interacciones
    # Argumento 'usuarios_interaccionados' debe ser ede este estilo
    #     [
    #         {
    #             "nombre_usuario": "ProjectStratos",
    #             "id": null,
    #             "interacciones": [
    #             {
    #                 "tipo": "retweet",
    #                 "id": "1373534612387926017",
    #                 "texto": "RT @ProjectStratos: Tenim bones notícies! Podreu veure les nostres conferències el dia 10 d'abril al nostre canal de YouTube. Si voleu sabe…",
    #                 "creado_en": "2021-03-21T07:19:05.000Z",
    #                 "idioma": "ca"
    #             }]
    #         },
    #         {..},
    #         {..}
    #     ]
    def lista_usuarios_interaccionados(usuarios_interaccionados) -> list:
        lista_usuarios_interaccionados = []

        for usuario in usuarios_interaccionados:
            tweets = 0
            retweets = 0
            respuestas = 0
            citas = 0

            for interaccion in usuario['interacciones']:
                if interaccion['tipo'] == 'tweet':
                    tweets += 1
                if interaccion['tipo'] == 'respuesta':
                    respuestas += 1
                elif interaccion['tipo'] == 'retweet':
                    retweets += 1
                elif interaccion['tipo'] == 'cita':
                    citas += 1

            lista_usuarios_interaccionados.append(
                {
                    'nombre_usuario': usuario['nombre_usuario'],
                    'total_interacciones': len(usuario['interacciones']),
                    'total_tweets': tweets,
                    'total_retweets': retweets,
                    'total_respuestas': respuestas,
                    'total_citas': citas
                })

        return lista_usuarios_interaccionados


class Tabla(object):
    @staticmethod
    def crear_tabla(tipo, titulo_archivo, columnas, filas, usuario_origen=None) -> None:
        tabla = pd.DataFrame(data=filas, columns=columnas)

        if tipo == 'interacciones-de-usuarioX':
            tabla['usuario_origen'] = usuario_origen

        print(tabla)

        # tabla.to_excel(excel_writer=titulo_archivo+'.xlsx', index=False)
        tabla.to_csv(path_or_buf=titulo_archivo+'.csv', index=False)


######################
# Funciones independiente
######################


# Cargar variables 'environment' para que se pueda
# acceder en todos los ficheros del programa.
def inicializar_variables_env():
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(dotenv_path=env_path)
