from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "¡Hola, soy Bruno, listo para ayudarte!"}

# Endpoint para verificar el webhook
@app.get("/webhook/")
async def verify_webhook(request: Request):
    """Verifica el webhook cuando Meta lo llama"""
    verify_token = "bruno_verify_token"  # Tu token de verificación
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        return int(challenge)
    else:
        return {"error": "No autorizado"}

# Endpoint para manejar mensajes de WhatsApp
@app.post("/webhook/")
async def whatsapp_webhook(request: Request):
    """Procesa los mensajes entrantes de WhatsApp"""
    try:
        data = await request.json()
        print("Datos recibidos desde WhatsApp:", data)

        # Verificar si hay mensajes
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
            texto = mensaje["text"]["body"]
            numero_cliente = mensaje["from"]

            print(f"Mensaje recibido: {texto} de {numero_cliente}")

            # Generar respuesta con OpenAI
            respuesta = generar_respuesta_bruno(texto)

            # Enviar respuesta a WhatsApp
            enviar_respuesta_whatsapp(numero_cliente, respuesta)
        else:
            print("No hay mensajes en la solicitud.")
        return {"status": "success"}
    except Exception as e:
        print("Error en el webhook:", e)
        return {"status": "error", "error": str(e)}

# Función para generar respuesta usando OpenAI
def generar_respuesta_bruno(texto_usuario):
    try:
        prompt_completo = """
        Eres Bruno, el asistente virtual de Ferrechingón. Ayuda a los clientes con consultas sobre productos, envíos y más.
        """
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": prompt_completo},
                {"role": "user", "content": texto_usuario}
            ],
            "max_tokens": 150
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            respuesta = response.json()["choices"][0]["message"]["content"]
            print("Respuesta generada por Bruno:", respuesta)
            return respuesta
        else:
            print("Error al llamar a OpenAI:", response.text)
            return "Lo siento, no puedo responder en este momento."
    except Exception as e:
        print("Error al generar respuesta:", e)
        return "Ocurrió un error al procesar tu consulta."

# Función para enviar respuesta a WhatsApp
def enviar_respuesta_whatsapp(numero_cliente, respuesta):
    try:
        whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_ID")  # Extraer desde las variables de entorno
        if not whatsapp_phone_id:
            whatsapp_phone_id = "505166682685328"  # ID de teléfono explícito como fallback
        
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
            print("Respuesta enviada exitosamente a WhatsApp.")
        else:
            print("Error al enviar respuesta a WhatsApp:", response.text)
    except Exception as e:
        print("Error al enviar respuesta a WhatsApp:", e)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render asigna dinámicamente el puerto
    uvicorn.run("main:app", host="0.0.0.0", port=port)
