import json


class Util:
    def get(self):
        return self

    def get_json(self):
        return json.dumps(self.__dict__)


class Usuario(Util):
    # Heredar métodos y atributos de la clase Util
    pass

    def __init__(self, id,
                 nombre_usuario,
                 nombre,
                 numero_seguidores,
                 numero_seguidos,
                 descripcion="",
                 url="",
                 tweets_sin_interacciones=[],
                 usuarios_interaccionados=[]
                 ):
        self.id = id
        self.nombre_usuario = nombre_usuario
        self.nombre = nombre
        self.numero_seguidores = numero_seguidores
        self.numero_seguidos = numero_seguidos
        # Quitar el carácter de cambio de línia "\n" en la descripción
        self.descripcion = descripcion.replace('\n', ' ')
        self.url = url
        self.tweets_sin_interacciones = tweets_sin_interacciones
        self.usuarios_interaccionados = usuarios_interaccionados


class UsuarioInteraccionado(Util):
    def __init__(self, nombre_usuario=None, id=None):
        self.nombre_usuario = nombre_usuario
        self.id = id
        self.interacciones = []

    def anadir_nombre_usuario(self, nombre_usuario):
        self.nombre_usuario = nombre_usuario

    def anadir_id_usuario(self, id):
        self.id = id

    # Argumento 'interaccion' debe ser tipo 'dict'
    def anadir_interaccion(self, interaccion):
        self.interacciones.append(interaccion)


class Interaccion(Util):
    # Heredar métodos y atributos de la clase Util
    pass

    def __init__(self, id, tipo, creado_en, idioma, texto):
        self.tipo = Interaccion.set_tipo(tipo)
        self.id = id
        self.texto = texto
        self.creado_en = creado_en
        self.idioma = idioma

    def set_tipo(tipo):
        if tipo == 'tweet':
            return 'tweet'
        elif tipo == 'replied_to':
            return 'respuesta'
        elif tipo == 'retweeted':
            return 'retweet'
        elif tipo == 'quoted':
            return 'cita'
