from woocommerce_integration import buscar_productos
from skydropx_integration import cotizar_envio
import requests
from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Usar la clave de OpenAI desde el entorno
api_key = os.getenv("OPENAI_API_KEY")
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Prompt completo para Bruno (desde el Prompt Persona)
prompt_completo = """
Eres Bruno, el asistente virtual de Ferrechingón. Tu objetivo es ayudar a los clientes respondiendo dudas sobre productos, envíos, y garantías. Sigues estas instrucciones:

1. Nunca mandes a los clientes a la competencia.
2. Responde preguntas ambiguas con lenguaje natural.
3. Consulta en tiempo real:
   - Catálogo de WooCommerce (productos, precios, existencias).
   - Fichas técnicas y manuales de usuario en las descripciones de los productos.
4. Calcula envíos usando Skydropx.
5. Si el cliente lo permite, guarda y recupera el historial de conversaciones.
6. Si no puedes resolver una duda, ofrece escalarla a un asesor humano.
7. Responde con empatía y profesionalismo.
8. Mantén un tono amigable y respetuoso, permitiendo plática ligera cuando sea apropiado.
"""

# Simulación de una consulta del cliente
consulta_usuario = "¿Qué herramientas tienen para cortar madera?"

# Buscar productos relacionados
productos = buscar_productos("madera", pagina=1, por_pagina=5)
productos_info = "\n".join([f"{p['name']} - ${p['price']}" for p in productos])

# Preparar mensaje para OpenAI
mensaje_usuario = f"{consulta_usuario}\n\nProductos relacionados:\n{productos_info}"

# Datos para OpenAI
data = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": prompt_completo},
        {"role": "user", "content": mensaje_usuario}
    ]
}

# Realizar la solicitud a OpenAI
response = requests.post(url, headers=headers, json=data)

# Procesar y mostrar la respuesta de OpenAI
if response.status_code == 200:
    print("Respuesta de Bruno:")
    print(response.json()["choices"][0]["message"]["content"])
else:
    print(f"Error al conectar con OpenAI: {response.status_code} - {response.text}")

# Probar la integración con Skydropx
origen = {
    "country_code": "MX",
    "postal_code": "45239",
    "area_level1": "Jalisco",
    "area_level2": "Zapopan",
    "area_level3": "Miguel de la Madrird Hurtado",
    "street1": "Avenida Prolongación López Mateos Sur 4460",
    "reference": "A un lado de Steren",
    "name": "Ferrechingón",
    "company": "Ferrechingón",
    "phone": "3343571098",
    "email": "ventas@ferrechingon.com"
}

destino = {
    "country_code": "MX",
    "postal_code": "72000",
    "area_level1": "Puebla",
    "area_level2": "Heroica Puebla de Zaragoza",
    "area_level3": "Centro",
    "street1": "Calle 3 Sur 104",
    "reference": "Frente al centro comercial",
    "name": "Juan Camanei",
    "company": "Panificadora La Flor SA de CV",
    "phone": "2222327645",
    "email": "cliente@ejemplo.com"
}

paquete = {
    "length": 7,
    "width": 29,
    "height": 25,
    "weight": 3
}

# Mostrar tarifas disponibles
tarifas = cotizar_envio(origen, destino, paquete)
if tarifas:
    print("\nOpciones de envío disponibles:")
    for tarifa in tarifas:
        print(f"{tarifa['provider_name']} - ${tarifa['cost']} MXN, entrega en {tarifa['days']} días.")
else:
    print("No se encontraron tarifas exitosas.")

