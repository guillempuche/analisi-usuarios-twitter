

from utils import  RecolectarUsuarios, inicializar_variables_env

def main():
    inicializar_variables_env()

    RecolectarUsuarios.buscar_usuarios_con_interacciones_y_guardar_en_archivos(
        ['ftsaez','balhisay','AgoraAbierta'])

if __name__ == "__main__":
    main()

