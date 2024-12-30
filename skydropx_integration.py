import time
import requests

# Credenciales de cliente de Skydropx Pro
client_id = "iEnvqn-VnHuwMvHdrqE8Uimq8s4HSZAwsc5txM1Eq74"  # Reemplaza con tu Client ID
client_secret = "5fpjXxTB58TWGWOE9k9YYJg5c-V6-lZi2sWPDDI_jUA"  # Reemplaza con tu Client Secret
auth_url = "https://pro.skydropx.com/api/v1/oauth/token"
cotizacion_url = "https://pro.skydropx.com/api/v1/quotations"

# Variables globales para el token
access_token = None
token_expiry_time = None

# Función para obtener un nuevo token de acceso
def obtener_token():
    global access_token, token_expiry_time
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(auth_url, headers=headers, json=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            token_expiry_time = time.time() + token_data["expires_in"]  # Guardar tiempo de expiración
            print(f"Nuevo token generado: {access_token}")
            return access_token
        else:
            print(f"Error al obtener token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error al conectar con Skydropx Pro: {e}")
        return None

# Función para verificar si el token es válido
def token_valido():
    if access_token and token_expiry_time and time.time() < token_expiry_time:
        return True
    return False

# Función para obtener un token válido (existente o nuevo)
def obtener_token_valido():
    if token_valido():
        return access_token
    else:
        return obtener_token()

# Función para realizar una cotización con Skydropx Pro
def cotizar_envio(origen, destino, paquete):
    token = obtener_token_valido()
    if not token:
        print("No se pudo obtener un token válido.")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Datos de la solicitud
    data = {
        "quotation": {
            "address_from": origen,
            "address_to": destino,
            "parcel": paquete
        }
    }

    try:
        response = requests.post(cotizacion_url, headers=headers, json=data)
        if response.status_code == 201:
            print("Cotización exitosa:")
            # Procesar tarifas exitosas
            cotizacion = response.json()
            rates = cotizacion.get("rates", [])
            tarifas_exitosas = [
                {
                    "provider_name": rate["provider_name"],
                    "cost": rate.get("total"),
                    "days": rate.get("days")
                }
                for rate in rates if rate["success"] and rate.get("total") is not None
            ]
            return tarifas_exitosas
        else:
            print(f"Error en la cotización: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error al realizar la cotización: {e}")
        return None






