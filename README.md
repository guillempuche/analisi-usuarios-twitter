## Iniciar programa

Pasos a seguir para arrancar el programa:
- Tener una [cuenta de desarrollador](https://developer.twitter.com/en/apply-for-access) de Twitter
- Crear un proyecto y una aplicación creados en el [dashboard de Twitter](https://developer.twitter.com/en/portal/dashboard).
- Descargar [Python](https://www.python.org/downloads/) (el código está testeado con la versión 3.9.1 de Python)
- Descargar proyecto y guardarlo a una carpeta
- Instalar librarías con estos comandos:
```
python -m pip install requests python-dotenv pandas openpyxl
```
Si no quieres crear archivos Excel (y solo  CSV), no hace falta que instales `openpyxl`
- Crear un archivo `.env` (en el directorio del programa) con las mismas variables que hay en el fichero de ejemplo `.env.example`. Rellenalas con los datos que estan en proyecto creado en la [web de la API de Twitter]
- Abrir el terminal de tu ordenador
- [Desdel terminal] Abrir entrar a la carpeta donde se encuentran los archivos del proyecto.
- [Desdel terminal] ...

## Documentación
- [API de Twitter para extraer historial de interacciones de un usuario](https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets) 
- [Estructura de los datos que recibes de la API de Twitter](https://developer.twitter.com/en/docs/twitter-api/data-dictionary/introduction)