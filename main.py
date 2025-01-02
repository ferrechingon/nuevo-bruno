from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from woocommerce_integration import buscar_productos, buscar_productos_paginados
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='bruno_logs.log')

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
        logging.info(f"Datos recibidos desde WhatsApp: {data}")

        if "messages" in data["entry"][0]["changes"][0]["value"]:
            mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
            texto = mensaje["text"]["body"]
            numero_cliente = mensaje["from"]

            logging.info(f"Mensaje recibido: {texto} de {numero_cliente}")

            # Generar respuesta usando el modelo de lenguaje
            respuesta = generar_respuesta_bruno(texto)

            # Enviar respuesta al cliente
            enviar_respuesta_whatsapp(numero_cliente, respuesta)
        else:
            logging.warning("No hay mensajes en la solicitud.")

        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error en el webhook: {e}")
        return {"status": "error", "error": str(e)}

# Función para generar respuesta usando OpenAI
def generar_respuesta_bruno(texto_usuario):
    try:
        # Leer el contenido del archivo de prompt
        with open("bruno_prompt.txt", "r", encoding="utf-8") as file:
            prompt_completo = file.read()

        # Loggear el prompt y la consulta del usuario
        logging.info(f"Prompt usado: {prompt_completo}")
        logging.info(f"Consulta del usuario: {texto_usuario}")

        # Consultar productos en WooCommerce
        productos = buscar_productos(texto_usuario)
        if productos:
            productos_info = "\n".join([
                f"{i+1}. {p['name']} - ${p['price']} MXN - [Ver producto]({p['permalink']})"
                for i, p in enumerate(productos)
            ])
            logging.info(f"Productos encontrados: {productos_info}")
            return (
                f"\u00a1Por supuesto! Los siguientes son algunas opciones relacionadas con tu consulta:\n\n"
                f"{productos_info}\n\n"
                f"Dale clic al enlace para ver m\u00e1s detalles del producto. \u00bfHay alguno que te interese o necesitas m\u00e1s ayuda?"
            )
        else:
            logging.info("No se encontraron productos para la consulta del usuario.")
            return (
                "Lo siento, no encontr\u00e9 productos relacionados con tu consulta. \u00bfQuieres intentar con otra b\u00fasqueda?"
            )

    except Exception as e:
        logging.error(f"Error al generar respuesta: {e}")
        return "Ocurri\u00f3 un error al procesar tu consulta. Por favor, intenta m\u00e1s tarde."

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
