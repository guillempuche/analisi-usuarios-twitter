

from os import path
from utils import Archivo, RecolectarUsuarios, inicializar_variables_env
from itertools import chain


def main():
    inicializar_variables_env()

    # IMPORTANTE: si el programa se inicia por primera vez,
    # debemos crear el fichero donde se guardará la información
    # de los usuarios.
    if path.exists('./base_de_datos/usuarios.json') == False:
        Archivo.guardar_a_archivo_json('usuarios', [])

    usuarios_base_datos = Archivo.leer_archivo_json(
        'usuarios')

    # IMPORTANTE: si no se tiene ningún usuario a la base de datos,
    # tenemos que añadir el primer usuario el primer usuario
    usuarios_nuevos = RecolectarUsuarios.buscar_usuarios_y_interacciones_no_existentes(
        usuarios_base_datos, 'nombre_usuario', ['sergidelmoral'])

    # Añadir los usuarios nuevos a en la base de datos.
    usuarios_base_datos = list(chain(usuarios_base_datos, usuarios_nuevos))

    Archivo.guardar_a_archivo_json(
        'usuarios', usuarios_base_datos)


if __name__ == "__main__":
    main()
