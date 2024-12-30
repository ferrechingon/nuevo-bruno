from woocommerce_integration import buscar_productos
import requests
from dotenv import load_dotenv
import os

# Cargar las variables desde el archivo .env
load_dotenv()

# Configurar clave de API
api_key = os.getenv("OPENAI_API_KEY")
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Prompt completo para Bruno
prompt_completo = """
Eres Bruno, el asistente virtual de Ferrechingón, una ferretería en línea. Tu objetivo es ayudar a los clientes respondiendo dudas sobre productos, envíos, y garantías. Sigue estas instrucciones:
1. Nunca mandes a los clientes a la competencia.
2. Responde preguntas ambiguas con lenguaje natural.
3. Consulta en tiempo real el catálogo de WooCommerce (productos, precios, existencias).
4. Si no puedes resolver una duda, ofrece escalarla a un asesor humano.
5. Responde con empatía y profesionalismo.
"""

# Simulación de una consulta del cliente
consulta_usuario = "¿Qué herramientas tienen para cortar madera?"

# Buscar productos relacionados
productos = buscar_productos("madera", pagina=1, por_pagina=5)
productos_info = "\n".join([f"{p['name']} - ${p['price']}" for p in productos])

# Preparar mensaje para Bruno
mensaje_usuario = f"{consulta_usuario}\n\nProductos relacionados:\n{productos_info}"

# Datos para OpenAI
data = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": prompt_completo},
        {"role": "user", "content": mensaje_usuario}
    ]
}

# Hacer la solicitud
response = requests.post(url, headers=headers, json=data)

# Procesar y mostrar la respuesta
if response.status_code == 200:
    print(response.json()["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code} - {response.text}")
