import json
import time
from os import path
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from itertools import chain
import csv

from api_twitter import Api
from modelos import UsuarioInteraccionado, Interaccion


class RecolectarDatos(object):
    # Buscar usuario según campo i el valor del campo
    @staticmethod
    def buscar_usuario_con_posicion(lista_usuarios, campo, valor) -> dict or None:
        if campo != 'nombre_usuario' and campo != 'id':
            raise ValueError('Argumento campo={} incorrecto'.format(campo))

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

    # Buscar listado de usuarios según campo y su correspondiente valor por cada usuario
    # Argumento 'campo' puede ser 'nombre_usuario' o 'id' y su argumento
    # 'valor' correspondiente.
    @staticmethod
    def buscar_usuarios_con_posiciones(usuarios, campo, valores) -> dict:
        lista = {
            'usuarios_no_encontrados': [],
            'usuarios_encontrados': []
        }

        if campo != 'nombre_usuario' and campo != 'id':
            raise ValueError(
                'Argumento campo={} no es "nombre_usuario" o "id"'.format(campo))
        if len(usuarios) == 0:
            print(
                'buscar_usuarios_con_posiciones - La lista de usuarios no contiene ningún usuario a buscar')
            lista['usuarios_no_encontrados'] = valores
            return lista

        for valor in valores:
            existe_usuario = RecolectarDatos.buscar_usuario_con_posicion(
                usuarios, campo, valor)

            if existe_usuario == None:
                lista['usuarios_no_encontrados'].append(valor)
            else:
                lista['usuarios_encontrados'].append({
                    'posicion': existe_usuario['posicion'],
                    'usuario':  existe_usuario['usuario']
                })

        print("De los {} usuarios a buscar, estos {} no estaban en la lista".format(
            len(valores), lista['usuarios_no_encontrados']))

        return lista

    # Recolectar usuarios y interacciones usuarios y sus interacciones en la base de datos, sino
    # existen ahí, recolectar información en la API de Twitter.
    # Argumento 'campo' solo puede ser 'nombre_usuario'
    # 'valor' correspondiente.
    @staticmethod
    def buscar_interacciones_de_usuarios(lista_referencia_usuarios=[], campo='', valores=[]) -> list:
        if (type(valores) is not list or len(valores) == 0 or campo != 'nombre_usuario'):
            raise ValueError(
                'Argumento campo={} o valores={} incorrectos'.format(campo, valores))

        usuarios_que_existen = []
        usuarios_nuevos = []

        # Comprobar si existe algun usuario en la lista local
        if len(lista_referencia_usuarios) > 0:
            # Comprobar qué usuarios ya existen en la lista de referencia
            for valor in valores:
                existe_usuario = RecolectarDatos.buscar_usuario_con_posicion(
                    lista_referencia_usuarios, campo, valor)
                usuarios_que_existen.append(existe_usuario['usuario'])

                if existe_usuario == None:
                    usuarios_nuevos.append(valor)

        if len(usuarios_nuevos) == 0:
            print(
                'Los usuarios que quieres buscar {} ya existen en la lista.'.format(valores))
        else:
            # Si no se ofrecen lista de referencia, se tendrán que buscar nuevos usuarios.
            usuarios_nuevos = valores

            # Obtener ids de los usuarios nuevso mediante la API de Twitter.
            usuarios_nuevos = Api.get_perfiles_usuarios_segun_nombre_usuario(
                usuarios_nuevos)

            # Debemos añadir las interacciones que ha tenido cada usuario
            # de la API de Twitter.
            for posicion, usuario in enumerate(usuarios_nuevos):
                historial_usuario = Api.get_historial_usuario(
                    usuario['id'])

                interacciones_filtradas = Filtro.categorizar_interacciones(
                    historial_usuario)

                # Añadir interacciones al usuario.
                usuarios_nuevos[posicion][
                    'usuarios_interaccionados'] = interacciones_filtradas['usuarios_interaccionados']
                usuarios_nuevos[posicion][
                    'tweets_sin_interacciones'] = interacciones_filtradas['tweets_sin_interacciones']

            # # Añadir los usuarios nuevos con sus historiales de interacción a la base de datos.
            # usuarios_base_datos = Archivo.leer_archivo_json(
            #     'usuarios_con_sus_interacciones')
            # usuarios_base_datos = list(
            #     chain(usuarios_base_datos, usuarios_nuevos))
            # Archivo.guardar_a_archivo_json(
            #     'usuarios_con_sus_interacciones', usuarios_base_datos)

        # Devolver usuarios a buscar con sus interacciones
        return usuarios_que_existen.extend(usuarios_nuevos)

    # Buscar interacciones de usuarios en Twitter, guardar todos los
    # datos en la base de datos 'usuarios_con_sus_interacciones' y
    # guardar las interacciones en la base de datos 'interacciones'.
    # Este método tiene en cuenta los usuarios duplicados y no los guarda
    # en las bases de datos.
    @staticmethod
    def buscar_usuarios_y_interacciones_y_guardar_en_archivos(lista_usuarios_a_buscar) -> None:
        if (type(lista_usuarios_a_buscar) is not list or len(lista_usuarios_a_buscar) == 0):
            raise ValueError(
                'Argumento list_usuarios_a_buscar={} es incorrecto'.format(lista_usuarios_a_buscar))

        # --------------------------------------
        # PASO 1: Buscar los perfiles de los usuarios nuevos y su historial
        # de interacción. Luego guardar los datos en la base de datos.

        # IMPORTANTE: si el programa se inicia por primera vez,
        # debemos crear la base de datos donde se guardará la información
        # de los usuarios.
        if path.exists('./base_de_datos/usuarios_con_sus_interacciones.json') == False:
            Archivo.guardar_a_archivo_json('usuarios', [])

        usuarios_base_datos = Archivo.leer_archivo_json(
            'usuarios_con_sus_interacciones')

        # Comprobar si los ususarios a buscar aún no estan en la base de datos.
        # Si no estan, recolectaremos sus datos en la API de Twitter y lo guardaremos
        # en la base de datos de usuarios
        usuarios = RecolectarDatos.buscar_usuarios_con_posiciones(
            usuarios_base_datos, 'nombre_usuario', lista_usuarios_a_buscar)

        if len(usuarios['usuarios_no_encontrados']) > 0:
            usuarios_nuevos = []
            perfiles_nuevos_usuarios = Api.get_perfiles_usuarios_segun_nombre_usuario(
                usuarios['usuarios_no_encontrados'])

            for u in perfiles_nuevos_usuarios:
                historial = Api.get_historial_usuario(u['id'])
                historial = Filtro.categorizar_interacciones(historial)
                # Combinar datos del perfil del usuario con su historial
                u |= historial  # merge operator
                usuarios_nuevos.append(u)

            # Añadir los usuarios nuevos con sus historiales de interacción a la base de datos.
            usuarios_base_datos = list(
                chain(usuarios_base_datos, usuarios_nuevos))
            Archivo.guardar_a_archivo_json(
                'usuarios_con_sus_interacciones', usuarios_base_datos)

        # guardar_información = RecolectarDatos.buscar_usuarios_con_posiciones(
        #     usuarios_encontrados, 'nombre_usuario', lista_usuarios_a_buscar)
        # if len(usuarios_nuevos) > 0:
        #     # Añadir los usuarios nuevos a en la base de datos.
        #     usuarios_base_datos = list(
        #         chain(usuarios_base_datos, usuarios_nuevos))
        #     Archivo.guardar_a_archivo_json(
        #         'usuarios_con_sus_interacciones', usuarios_base_datos)

        # --------------------------------------
        # PASO 2: Guardarlas interacciones de los usuarios a buscar en la
        # base de datos de interacciones

        # IMPORTANTE: si el programa se inicia por primera vez,
        # debemos crear el fichero donde se guardará la información
        # de los usuarios.
        if path.exists('./base_de_datos/interaccciones.json') == False:
            Archivo.guardar_a_archivo_json(
                'interacciones', [])

        todas_las_interacciones = Archivo.leer_archivo_json('interacciones')
        tabla_completa = Tabla(columnas=['nombre_usuario', 'total_interacciones',
                                         'total_tweets', 'total_retweets',
                                         'total_respuestas', 'total_citas',
                                         'usuario_origen'])

        for usuario_a_buscar in lista_usuarios_a_buscar:
            # ##### Obtener perfiles de usuarios analizados y crear la tabla en un fichero CSV
            # filas = []
            # for usuario in usuarios_base_datos:
            #     filas.append([
            #         usuario['id'],
            #         usuario['nombre_usuario'],
            #         usuario['nombre'],
            #         usuario['numero_seguidores'],
            #         usuario['numero_seguidos'],
            #         'https://twitter.com/'+usuario['nombre_usuario']
            #     ])
            # Tabla.crear_tabla(tipo='perfiles-usuarios',
            #                 titulo_archivo='./base_de_datos/perfiles-usuarios-_con_interacciones_analizados',
            #                 columnas=['id_twitter', 'nombre_usuario', 'nombre',
            #                             'numero_seguidores', 'numero_seguidos', 'url_perfil'],
            #                 filas=filas)

            usuario_encontrado = RecolectarDatos.buscar_usuario_con_posicion(
                todas_las_interacciones, 'nombre_usuario', usuario_a_buscar)

            if usuario_encontrado is None:
                # raise ValueError(
                #     'Usuario {} no encontrado en la base de datos'.format(usuario_a_buscar))
                posicion = usuario_encontrado['posicion']

                usuario_origen = usuario_encontrado['usuario']['nombre_usuario']

                usuarios_interaccionados = usuarios_base_datos[
                    posicion]['usuarios_interaccionados']

                # print(usuarios_interaccionados[0])

                interacciones = Filtro.lista_usuarios_interaccionados(
                    usuarios_interaccionados, usuario_origen)

                todas_las_interacciones.extend(interacciones)

                filas = []

                for usuario in interacciones:
                    filas.append([
                        usuario['nombre_usuario'],
                        usuario['total_interacciones'],
                        usuario['total_tweets'],
                        usuario['total_retweets'],
                        usuario['total_respuestas'],
                        usuario['total_citas'],
                        usuario['usuario_origen']
                    ])

                # La tabla contiene las interacciones de la base
                # de datos junto a las nuevas interacciones.
                tabla = Tabla(
                    columnas=['nombre_usuario', 'total_interacciones', 'total_tweets',
                              'total_retweets', 'total_respuestas', 'total_citas', 'usuario_origen'],
                    filas=filas
                )
                tabla_completa['filas'].extend(tabla['filas'])

        # Guardar todas las interacciones en un archvo JSON y otro CSV
        Archivo.guardar_a_archivo_json(
            'interacciones',
            todas_las_interacciones)
        Archivo.guardar_a_archivo_csv('interacciones',
                                      columnas=tabla_completa['columnas'],
                                      filas=tabla_completa['filas'])

    # Buscar perfiles de usuarios (se filtran los duplicados)
    @staticmethod
    def buscar_perfiles_usuarios_y_guardar_en_archivo(nombres_usuarios) -> None:
        if type(nombres_usuarios) != list or len(nombres_usuarios) == 0:
            raise ValueError(
                'Argumento alores={} es incorrecto'.format(nombres_usuarios))

        # IMPORTANTE: si el programa se inicia por primera vez,
        # debemos crear el fichero donde se guardará la información
        # de los usuarios.
        if path.exists('./base_de_datos/perfiles_usuarios.json') == False:
            Archivo.guardar_a_archivo_json(
                'perfiles_usuarios', [])

        todos_perfiles_usuarios = Archivo.leer_archivo_json(
            'perfiles_usuarios')

        # Comprobar los usuarios que ya existen para no duplicarlos
        busqueda_de_usuarios = RecolectarDatos.buscar_usuarios_con_posiciones(
            todos_perfiles_usuarios, 'nombre_usuario', nombres_usuarios)

        usuarios_no_encontrados = busqueda_de_usuarios['usuarios_no_encontrados']

        if len(usuarios_no_encontrados) == 0:
            print('Todos los usuarios ya estan en la base de datos "perfiles_usuarios"')
            return None

        nuevos_perfiles_usuarios = Api.get_perfiles_usuarios_segun_nombre_usuario(
            usuarios_no_encontrados)

        # Añadir los usuarios nuevos con sus historiales de interacción a la base de datos.
        todos_perfiles_usuarios = list(
            chain(todos_perfiles_usuarios, nuevos_perfiles_usuarios))
        Archivo.guardar_a_archivo_json(
            'perfiles_usuarios', todos_perfiles_usuarios)

        # Columnas para poner en el archivo CSV.
        columnas = ['id', 'nombre_usuario', 'nombre',
                    'numero_seguidores', 'numero_seguidos', 'descripcion', 'url', 'localidad']
        # Guardar todos valores de cada campo de cada usuario en una lista de filas.
        filas = []
        for perfil in todos_perfiles_usuarios:
            filas.append([
                perfil['id'],
                perfil['nombre_usuario'],
                perfil['nombre'],
                perfil['numero_seguidores'],
                perfil['numero_seguidos'],
                perfil['descripcion'],
                perfil['url'],
                perfil['localidad'],
            ])

        Archivo.guardar_a_archivo_csv('perfiles_usuarios', columnas, filas)


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
                            existe_usuario = RecolectarDatos.buscar_usuario_con_posicion(
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
    def lista_usuarios_interaccionados(usuarios_interaccionados, usuario_origen) -> list:
        if (type(usuarios_interaccionados) != list
                or len(usuarios_interaccionados) == 0
                or type(usuario_origen) != str):
            raise ValueError('Argumento usuarios_interaccionados ({}) o usuario_origen={} es incorrecto'.format(
                type(usuarios_interaccionados), usuario_origen))

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
                    'total_citas': citas,
                    'usuario_origen': usuario_origen
                })

        return lista_usuarios_interaccionados

    @staticmethod
    # Argumento 'lista' debe contener valores
    def eliminar_elementos_string_duplicados_en_lista(lista) -> list:
        if type(lista) != list or len(lista) == 0:
            raise ValueError(
                'Argumento "lista" no es tipo lista o no tiene valores')

        lista_limpiada = []

        # Método List Comprehension
        [lista_limpiada.append(elemento)
         for elemento in lista if elemento not in lista_limpiada]

        return lista_limpiada


class Archivo(object):
    # Argumento 'tipo_de_datos' tiene que explicar qué tipo de datos se guardan
    # Argumento 'datos_dict' tiene que ser tipo 'dict' (dictionary)
    @ staticmethod
    def guardar_a_archivo_json(nombre_archivo, datos_dict):
        with open('./base_de_datos/{}.json'
                  .format(nombre_archivo), 'w') as archivo:
            json.dump(datos_dict, archivo)

    @ staticmethod
    # Obtener archivo que contenga JSON y convertirlo a formato dict.
    # Argumento 'nombre_archivo' es necesario y el archivo para leer
    # debe estar en la carpeta 'base_de_datos'. La nombre no debe contener
    # no el tipo de formato, es decir, no debe contener '.json'.
    def leer_archivo_json(nombre_archivo) -> dict:
        with open('./base_de_datos/{}.json'
                  .format(nombre_archivo), 'r', encoding='utf-8') as archivo:
            datos_json = archivo.read()
            datos = json.loads(datos_json)

        return datos

    @ staticmethod
    # Obtener archivo que contenga JSON y convertirlo a formato dict.
    # Argumento 'nombre_archivo' es necesario y el archivo para leer
    # debe estar en la carpeta 'base_de_datos'. La nombre no debe contener
    # no el tipo de formato, es decir, no debe contener '.json'.
    def leer_archivo_csv(nombre_archivo) -> dict:
        data_frame = pd.read_csv(
            './base_de_datos/{}.csv'.format(nombre_archivo))

        # print(data_frame.to_dict)
        data_frame['nombre_usuario']

        # with open('./base_de_datos/{}.csv'.format(nombre_archivo), newline='') as archivo:
        #     reader = csv.DictReader(archivo)
        #     print(reader)
        #     # for row in reader:
        #     # print(row['first_name'], row['last_name'])
        #     return reader

    @staticmethod
    def guardar_a_archivo_csv(nombre_archivo, columnas, filas):
        with open('./base_de_datos/{}.csv'
                  .format(nombre_archivo), 'w', newline='', encoding="utf-8") as archivo:
            writer = csv.writer(archivo, delimiter=',', strict=True)
            writer.writerow(columnas)
            writer.writerows(filas)


class Tabla(object):
    def __new__(self, columnas=[], filas=[]) -> object:
        tabla = pd.DataFrame(data=filas, columns=columnas)

        tabla = {
            'columnas': tabla.columns.values.tolist() if len(columnas) > 0 else [],
            'filas': tabla.values if len(filas) > 0 else []
        }

        return tabla

    # @staticmethod
    # def crear_tabla_y_guardar_archivo_csv(titulo_archivo, columnas, filas) -> None:
    #     tabla = Tabla.crear_tabla(columnas, filas)

    #     # tabla.to_excel(excel_writer=titulo_archivo+'.xlsx', index=False)
    #     tabla.to_csv(path_or_buf=titulo_archivo+'.csv', index=False)

    #     print('Tabla guardada exitosamente en archivo CSV')


class Tiempo(object):
    def __new__(_):
        tiempo = time.localtime()
        return '{año}-{mes}-{dia} {hora}.{min}.{seg}'.format(año=tiempo.tm_year, mes=tiempo.tm_mon,
                                                             dia=tiempo.tm_mday, hora=tiempo.tm_hour,
                                                             min=tiempo.tm_min, seg=tiempo.tm_sec)


######################
# Funciones independiente
######################


# Cargar variables 'environment' para que se pueda
# acceder en todos los ficheros del programa.
def inicializar_variables_env():
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(dotenv_path=env_path)
