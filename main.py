from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from woocommerce_integration import buscar_productos, buscar_productos_paginados


# Cargar variables de entorno
load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "¡Hola, soy Bruno, listo para ayudarte!"}

# Endpoint para manejar mensajes de WhatsApp
@app.post("/webhook/")
async def whatsapp_webhook(request: Request):
    """Procesa los mensajes entrantes de WhatsApp"""
    try:
        data = await request.json()
        print("Datos recibidos desde WhatsApp:", data)

        if "messages" in data["entry"][0]["changes"][0]["value"]:
            mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
            texto = mensaje["text"]["body"]
            numero_cliente = mensaje["from"]

            print(f"Mensaje recibido: {texto} de {numero_cliente}")

            # Generar respuesta usando el modelo de lenguaje
            respuesta = generar_respuesta_bruno(texto)

            # Enviar respuesta al cliente
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
        # Leer el contenido del archivo de prompt
        with open("bruno_prompt.txt", "r", encoding="utf-8") as file:
            prompt_completo = file.read()

        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": prompt_completo},
                {"role": "user", "content": texto_usuario}
            ],
            "max_tokens": 300
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429 or "insufficient_quota" in response.text:
            notificar_creditos_agotados()
            return "Lo siento, no puedo responder en este momento debido a un problema técnico."
        else:
            print("Error al llamar a OpenAI:", response.text)
            return "Lo siento, no puedo responder en este momento."
    except Exception as e:
        print("Error al generar respuesta:", e)
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
            print("Respuesta enviada exitosamente a WhatsApp.")
        else:
            print("Error al enviar respuesta a WhatsApp:", response.text)
    except Exception as e:
        print("Error al enviar respuesta a WhatsApp:", e)

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
                print("Notificación enviada por WhatsApp.")
            else:
                print("Error al enviar notificación por WhatsApp:", response.text)
    except Exception as e:
        print("Error al enviar notificación de créditos agotados:", e)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
