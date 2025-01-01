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

            # Determinar la intención del mensaje
            intencion = determinar_intencion(texto)
            print(f"Intención detectada: {intencion}")

            # Canalizar a la función adecuada según la intención
            if intencion == "búsqueda de producto":
                respuesta = manejar_busqueda_productos(texto)
            elif intencion == "consulta de envío":
                respuesta = manejar_cotizacion_envio(texto)
            else:
                # Predeterminado a conversación casual
                respuesta = manejar_conversacion_casual(texto)

            # Enviar respuesta al cliente
            enviar_respuesta_whatsapp(numero_cliente, respuesta)
        else:
            print("No hay mensajes en la solicitud.")

        return {"status": "success"}
    except Exception as e:
        print("Error en el webhook:", e)
        return {"status": "error", "error": str(e)}

# Función para determinar intención del mensaje
def determinar_intencion(texto_usuario):
    try:
        prompt = f"""
Eres un modelo avanzado de lenguaje natural. Tu tarea es analizar el siguiente texto y determinar la intención del usuario. Las posibles intenciones son:
- Búsqueda de producto
- Consulta de envío
- Conversación casual
- Otra

Texto: "{texto_usuario}"

Devuelve solo la intención como una de las categorías anteriores.
"""
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Eres un clasificador de intenciones de texto."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 10
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip().lower()
        elif response.status_code == 429 or "insufficient_quota" in response.text:
            notificar_creditos_agotados()
            return "conversación casual"
        else:
            print("Error al determinar intención:", response.text)
            return "conversación casual"
    except Exception as e:
        print("Error al determinar intención:", e)
        return "conversación casual"


# Función para manejar búsquedas de productos
def manejar_busqueda_productos(texto_usuario):
    try:
        productos = buscar_productos_paginados(texto_usuario)
        if productos:
            productos_info = "\n".join([
                f"{p['name']} - ${p['price']} - [Ver producto]({p['permalink']})" for p in productos[:10]
            ])
            return (
                "Buscando en el catálogo de productos de Ferrechingón\n\n"
                f"Aquí tienes algunas opciones relacionadas con tu consulta:\n{productos_info}\n\n"
                "¿Te gustaría más información sobre alguno de estos productos?"
            )
        else:
            return "Lo siento, no encontré productos relacionados con tu consulta. ¿Quieres intentar con otra búsqueda?"
    except Exception as e:
        print("Error al manejar búsqueda de productos:", e)
        return "Ocurrió un error al buscar productos. Por favor, intenta más tarde."

# Función para manejar cotización de envíos
def manejar_cotizacion_envio(texto_usuario):
    return "Esta funcionalidad aún está en desarrollo. Próximamente podrás cotizar envíos aquí."

# Función para manejar conversaciones casuales
def manejar_conversacion_casual(texto_usuario):
    return "¡Gracias por tu mensaje! ¿En qué más puedo ayudarte hoy?"

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

        # Enviar notificación por correo electrónico
        #email_from = os.getenv("EMAIL_FROM")
        #email_to = os.getenv("EMAIL_TO")
        #email_password = os.getenv("EMAIL_PASSWORD")

        #if email_from and email_to and email_password:
        #    msg = MIMEText(mensaje)
        #    msg['Subject'] = "Alerta: Créditos de OpenAI agotados"
        #    msg['From'] = email_from
        #    msg['To'] = email_to

        #    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        #        server.starttls()
        #        server.login(email_from, email_password)
        #        server.sendmail(email_from, email_to, msg.as_string())
        #        print("Notificación enviada por correo electrónico.")

        # Enviar notificación por WhatsApp
        whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_ID')
        #admin_phone_number = os.getenv('ADMIN_PHONE_NUMBER')
        admin_phone_number = "5213333597991"

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
