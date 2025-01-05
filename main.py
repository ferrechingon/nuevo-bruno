from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from db import guardar_mensaje, obtener_historial
from woocommerce_integration import buscar_productos_paginados
import logging
import json

# Configurar logging para que envíe los mensajes a la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "¡Hola, soy Bruno, listo para ayudarte!"}

# Cargar el prompt inicial desde el archivo
def cargar_prompt():
    try:
        with open("bruno_prompt.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logging.error("El archivo bruno_prompt.txt no se encontró.")
        return ""

# Función para truncar historial si excede el límite de tokens permitido
def truncar_historial(historial, max_tokens):
    total_tokens = sum(len(m.get("content", "")) for m in historial)
    while total_tokens > max_tokens and len(historial) > 1:
        historial.pop(0)
        total_tokens = sum(len(m.get("content", "")) for m in historial)
    return historial

@app.post("/webhook/")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"Datos recibidos: {data}")

        # Verificar si el payload contiene mensajes
        if "messages" not in data["entry"][0]["changes"][0]["value"]:
            logging.info("El payload no contiene mensajes. Ignorando el evento.")
            return {"status": "ignored"}

        mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
        texto = mensaje.get("text", {}).get("body", "").strip()
        numero_cliente = mensaje.get("from", "")

        if not texto:
            logging.info("El mensaje está vacío. Ignorando.")
            return {"status": "ignored"}

        if not numero_cliente:
            logging.info("Número de cliente no encontrado. Ignorando el evento.")
            return {"status": "ignored"}

        # Recuperar historial antes de guardar el mensaje
        historial = obtener_historial(numero_cliente)

        # Verificar si no hay historial y agregar el prompt inicial
        if not historial:
            prompt = cargar_prompt()
            if not prompt:
                logging.error("No se pudo cargar el prompt inicial.")
                return {"error": "No se pudo cargar el prompt inicial."}

            logging.info(f"Prompt cargado: {prompt}")
            historial_contexto = [{"role": "system", "content": prompt}]
            guardar_mensaje(numero_cliente, "system", prompt)
        else:
            historial_contexto = [{"role": msg["message_role"], "content": msg["message_content"]} for msg in historial]

        # Añadir el mensaje actual del usuario al historial
        historial_contexto.append({"role": "user", "content": texto})

        # Truncar historial si excede el límite de tokens permitido
        historial_contexto = truncar_historial(historial_contexto, max_tokens=7692)

        # Guardar el mensaje del usuario en la base de datos
        guardar_mensaje(numero_cliente, "user", texto)

        # Construir el payload para la llamada a OpenAI
        payload = {
            "model": "gpt-4-0613",
            "messages": historial_contexto,
            "functions": [
                {
                    "name": "buscar_productos",
                    "description": "Busca productos en el catálogo de WooCommerce según palabras clave proporcionadas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Palabras clave para buscar productos."},
                            "pagina": {"type": "integer", "description": "Número de la página a consultar."},
                            "por_pagina": {"type": "integer", "description": "Cantidad de resultados por página."}
                        },
                        "required": ["query"]
                    }
                }
            ],
            "function_call": "auto"
        }

        # Llamar a la API de OpenAI
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            logging.error(f"Error al llamar a OpenAI: {response.status_code}, {response.text}")
            respuesta = "Lo siento, no pude procesar tu solicitud. Por favor intenta de nuevo más tarde."
        else:
            respuesta_json = response.json()
            choice = respuesta_json.get("choices", [{}])[0].get("message", {})
            if choice.get("function_call"):
                function_name = choice["function_call"]["name"]
                function_args = json.loads(choice["function_call"]["arguments"])
                if function_name == "buscar_productos":
                    productos = buscar_productos_paginados(function_args["query"], function_args.get("pagina", 1), function_args.get("por_pagina", 5))
                    respuesta = "\n".join([f"{p['name']} - {p['permalink']}" for p in productos]) if productos else "No se encontraron productos."
                else:
                    respuesta = "Lo siento, no pude procesar tu solicitud."
            else:
                respuesta = choice.get("content", "Lo siento, no pude procesar tu solicitud.")

        # Guardar la respuesta de Bruno en la base de datos
        guardar_mensaje(numero_cliente, "assistant", respuesta)

        # Enviar la respuesta al usuario por WhatsApp
        enviar_respuesta_whatsapp(numero_cliente, respuesta)

        return {"status": "success"}

    except KeyError as e:
        logging.error(f"Error de clave en los datos recibidos: {e}")
        return {"error": "Estructura inesperada en el payload"}
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        return {"error": "Error en el servidor"}

# Función de ejemplo para enviar respuestas a WhatsApp
def enviar_respuesta_whatsapp(numero_cliente, mensaje):
    url = f"https://graph.facebook.com/v16.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_cliente,
        "type": "text",
        "text": {"body": mensaje}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logging.error(f"Error al enviar mensaje a WhatsApp: {response.status_code}, {response.text}")
        else:
            logging.info("Respuesta enviada exitosamente a WhatsApp.")
    except Exception as e:
        logging.error(f"Error al intentar enviar mensaje a WhatsApp: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render asigna el puerto a la variable de entorno PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)
