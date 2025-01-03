from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from woocommerce_integration import buscar_productos, buscar_productos_paginados
from db import guardar_mensaje, obtener_historial
import logging

# Configurar logging para que envíe los mensajes a la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "¡Hola, soy Bruno, listo para ayudarte!"}

# Endpoint para manejar mensajes de WhatsApp
@app.post("/webhook/")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        print(f"Datos recibidos: {data}")

        # Verificar si el payload contiene mensajes
        if "messages" not in data["entry"][0]["changes"][0]["value"]:
            print("El payload no contiene mensajes. Ignorando el evento.")
            return {"status": "ignored"}

        mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
        texto = mensaje.get("text", {}).get("body", "").strip()
        numero_cliente = mensaje.get("from", "")

        if not texto:
            print("El mensaje está vacío. Ignorando.")
            return {"status": "ignored"}

        if not numero_cliente:
            print("Número de cliente no encontrado. Ignorando el evento.")
            return {"status": "ignored"}

        # Recuperar historial antes de guardar el mensaje actual
        historial = obtener_historial(numero_cliente)

        # Crear contexto inicial si no hay historial previo
        if not historial:
            prompt = cargar_prompt()
            print(f"Prompt cargado: {prompt}")  # Debug temporal
            historial_contexto = [{"role": "system", "content": prompt}]
        else:
            historial_contexto = [{"role": msg["message_role"], "content": msg["message_content"]} for msg in historial]

        # Añadir el mensaje actual del usuario al historial
        historial_contexto.append({"role": "user", "content": texto})

        # Guardar el mensaje del usuario en la base de datos
        guardar_mensaje(numero_cliente, "user", texto)

        # Enviar historial completo a OpenAI
        print(f"Historial enviado a OpenAI: {historial_contexto}")
        respuesta = generar_respuesta_bruno(historial_contexto)
        print(f"Respuesta generada: {respuesta}")

        # Guardar la respuesta de Bruno en la base de datos
        guardar_mensaje(numero_cliente, "assistant", respuesta)

        # Enviar la respuesta al usuario por WhatsApp
        enviar_respuesta_whatsapp(numero_cliente, respuesta)

    except KeyError as e:
        print(f"Error de clave en los datos recibidos: {e}")
        return {"error": "Estructura inesperada en el payload"}
    except Exception as e:
        print(f"Error inesperado: {e}")
        return {"error": "Error en el servidor"}










# Función para generar respuesta usando OpenAI
def generar_respuesta_bruno(historial_contexto):
    try:
        # Configurar la solicitud a OpenAI
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4",
            "messages": historial_contexto,
            "max_tokens": 150,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return response_data["choices"][0]["message"]["content"]
        else:
            logging.error(f"Error en OpenAI API: {response.status_code}, {response.text}")
            return "Lo siento, hubo un problema al procesar tu consulta."
    except Exception as e:
        logging.error(f"Error al generar respuesta: {e}")
        return "Ocurrió un error al procesar tu consulta. Por favor, intenta más tarde."




# Función para enviar respuesta a WhatsApp
def enviar_respuesta_whatsapp(numero_cliente, respuesta):
    try:
        whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_ID')
        url = f"https://graph.facebook.com/v16.0/{whatsapp_phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_cliente,
            "type": "text",
            "text": {"body": respuesta}
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logging.info("Respuesta enviada exitosamente a WhatsApp.")
        else:
            logging.error(f"Error al enviar respuesta a WhatsApp: {response.text}")
    except Exception as e:
        logging.error(f"Error al enviar respuesta a WhatsApp: {e}")

# Función para notificar que los créditos de OpenAI están agotados
def notificar_creditos_agotados():
    try:
        mensaje = "Los créditos de OpenAI se han agotado. Por favor, recarga para evitar interrupciones."

        # Enviar notificación por WhatsApp
        whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_ID')
        admin_phone_number = os.getenv('5213333597991')

        if whatsapp_phone_id and admin_phone_number:
            url = f"https://graph.facebook.com/v16.0/{whatsapp_phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": admin_phone_number,
                "type": "text",
                "text": {"body": mensaje}
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                logging.info("Notificación enviada por WhatsApp.")
            else:
                logging.error(f"Error al enviar notificación por WhatsApp: {response.text}")
    except Exception as e:
        logging.error(f"Error al enviar notificación de créditos agotados: {e}")


def truncar_historial(historial, max_tokens=3000):
    def calcular_tokens(messages):
        return sum(len(m["content"].split()) for m in messages)

    while calcular_tokens(historial) > max_tokens:
        if len(historial) > 1 and historial[0]["role"] == "system":
            historial.pop(1)  # Mantén el mensaje "system"
        else:
            historial.pop(0)
    return historial



   

def cargar_prompt():
    try:
        with open("bruno_prompt.txt", "r", encoding="utf-8") as archivo:
            prompt = archivo.read()
            print(f"Prompt cargado: {prompt}")  # Debug temporal
            return prompt
    except FileNotFoundError:
        print("El archivo bruno_prompt.txt no se encontró.")
        return (
            "Eres Bruno, un asistente virtual para Ferrechingón. Ayudas a responder preguntas sobre productos, precios, "
            "envíos y políticas de la tienda. Tu personalidad es amigable, profesional y útil."
        )



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
