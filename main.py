

from utils import Archivo, Filtro, RecolectarDatos, inicializar_variables_env
import pandas
from os import path


def main():
    inicializar_variables_env()

    # Obtener nombres usuarios
    # nombres_usuarios = ['sergidelmoral', 'hruizmartin',
    #                     'c_magro', 'ftsaez', 'balhisay', 'AgoraAbierta']

    # Otener nombres usuarios de un fichero descargado de Google Data Studio
    data_frame = pandas.read_csv('./base_de_datos/datastudio.csv')
    nombres_usuarios = list(data_frame['nombre_usuario'])
    nombres_usuarios = Filtro.eliminar_elementos_string_duplicados_en_lista(
        nombres_usuarios)
    print(nombres_usuarios)

    # for i in interacciones:
    #     nombres_usuarios.append(i['nombre_usuario'])

    # # Añade los nombres de usuarios de Twitter (se puede ver en la URL de Twitter
    # # eg: https://twitter.com/ftsaez) que quieres analizar
    # RecolectarDatos.buscar_usuarios_y_interacciones_y_guardar_en_archivos(
    #     nombres_usuarios)

    RecolectarDatos.buscar_perfiles_usuarios_y_guardar_en_archivo(
        nombres_usuarios)

    perfiles = Archivo.leer_archivo_json('perfiles_usuarios')
    # Columnas para poner en el archivo CSV.
    columnas = ['id', 'nombre_usuario', 'nombre',
                'numero_seguidores', 'numero_seguidos', 'descripcion', 'url']
    # Guardar todos valores de cada campo de cada usuario en una lista de filas.
    filas = []
    for perfil in perfiles:
        filas.append([
            perfil['id'],
            perfil['nombre_usuario'],
            perfil['nombre'],
            perfil['numero_seguidores'],
            perfil['numero_seguidos'],
            perfil['descripcion'],
            perfil['url'],
        ])
    Archivo.guardar_a_archivo_csv('perfiles_usuarios', columnas, filas)

    # RecolectarDatos.buscar_usuarios_con_posiciones()
    # RecolectarDatos.buscar_perfiles_usuarios_y_guardar_en_archivo(
    #     ['ftsaez','balhisay','AgoraAbierta'])


if __name__ == "__main__":
    main()
