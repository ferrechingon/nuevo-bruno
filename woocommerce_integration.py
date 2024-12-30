import requests
from requests.auth import HTTPBasicAuth

# Credenciales de WooCommerce
consumer_key = "ck_2f6025cca8275b04b14bfaca9138223922d10894"  # Reemplaza con tu clave
consumer_secret = "cs_f09a660057897ad158920d33f31c014f1b5771a0"  # Reemplaza con tu clave
woocommerce_url = "https://www.ferrechingon.com/wp-json/wc/v3/products"

# Función para obtener productos con paginación
def obtener_productos(pagina=1, por_pagina=100):
    try:
        # Parámetros para la paginación
        params = {
            "page": pagina,
            "per_page": por_pagina  # Límite máximo es 100 por página
        }

        # Realiza la solicitud
        response = requests.get(
            woocommerce_url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            params=params
        )

        if response.status_code == 200:
            productos = response.json()
            return productos
        else:
            print(f"Error al consultar productos: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"Error en la conexión: {e}")
        return []

# Función para buscar productos por palabras clave
def buscar_productos(palabra_clave, pagina=1, por_pagina=100):
    try:
        params = {
            "search": palabra_clave,
            "page": pagina,
            "per_page": por_pagina
        }
        response = requests.get(
            woocommerce_url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            params=params
        )
        if response.status_code == 200:
            productos = response.json()
            return productos
        else:
            print(f"Error al buscar productos: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"Error en la conexión: {e}")
        return []
