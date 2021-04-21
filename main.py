

from utils import Archivo, Filtro, RecolectarDatos, inicializar_variables_env
import pandas
from os import path


def main():
    # -----------------------------------
    # INICIAR VARABLES ENVIRONMENT
    inicializar_variables_env()

    # -----------------------------------
    # INICIAR USUARIO DE TWITTER A BUSCAR
    # Lista de nombres usuarios a buscar
    nombres_usuarios = ['inmitacs', 'profesmadeinuk', 'tonisolano']

    # -----------------------------------
    # OPCIÓN A: Añade los nombres de usuarios de Twitter (se puede ver en la URL de Twitter
    # eg: https://twitter.com/ftsaez) que quieres analizar
    RecolectarDatos.buscar_usuarios_y_interacciones_y_guardar_en_archivos(
        nombres_usuarios)

    # -----------------------------------
    # OPCIÓN B: Buscar información de los perfiles de los usuarios
    interacciones = Archivo.leer_archivo_json('interacciones')
    for i in interacciones:
        nombres_usuarios.append(i['nombre_usuario'])
    RecolectarDatos.buscar_perfiles_usuarios_y_guardar_en_archivo(
        nombres_usuarios)

    # ------------------------
    # PARA ARREGLAR ERRORES EN LAS BASES DE DATOS

    # perfiles = Archivo.leer_archivo_json('perfiles_usuarios')
    # perfiles_arreglados = []
    # for perfil in perfiles:
    #     perfil['localidad'] = ""
    #     perfiles_arreglados.append(perfil)
    # Archivo.guardar_a_archivo_json(
    #     'perfiles_usuarios', perfiles_arreglados)

    # # Columnas para poner en el archivo CSV.
    # columnas = ['id', 'nombre_usuario', 'nombre',
    #             'numero_seguidores', 'numero_seguidos', 'descripcion', 'url', 'localidad']
    # # Guardar todos valores de cada campo de cada usuario en una lista de filas.
    # filas = []
    # for perfil in perfiles:
    #     filas.append([
    #         perfil['id'],
    #         perfil['nombre_usuario'],
    #         perfil['nombre'],
    #         perfil['numero_seguidores'],
    #         perfil['numero_seguidos'],
    #         perfil['descripcion'],
    #         perfil['url'],
    #         perfil['localidad'],
    #     ])
    # Archivo.guardar_a_archivo_csv('perfiles_usuarios', columnas, filas)

    # Otener nombres usuarios de un fichero descargado de Google Data Studio
    # data_frame = pandas.read_csv('./base_de_datos/datastudio.csv')
    # nombres_usuarios = list(data_frame['nombre_usuario'])


if __name__ == "__main__":
    main()
