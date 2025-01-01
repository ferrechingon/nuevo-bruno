from fastapi import FastAPI, Request
import requests
import os
from dotenv import load_dotenv
from woocommerce_integration import buscar_productos

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

            # Generar palabras clave utilizando OpenAI
            palabras_clave = extraer_palabras_clave(texto)
            print(f"Palabras clave extraídas: {palabras_clave}")

            # Intentar buscar productos en WooCommerce usando las palabras clave
            productos = buscar_productos(palabras_clave)

            if not productos:
                # Ampliar términos de búsqueda con OpenAI
                print("No se encontraron productos. Ampliando términos de búsqueda.")
                nuevos_terminos = generar_terminos_relacionados(texto)
                print(f"Términos relacionados generados: {nuevos_terminos}")
                productos = buscar_productos(nuevos_terminos)

            if productos:
                print(f"Productos encontrados: {productos}")
                productos_info = "\n".join([f"{p['name']} - ${p['price']}" for p in productos])
                respuesta = (
                    f"Buscando en el catálogo de productos de Ferrechingón\n\n"
                    f"Aquí tienes algunas opciones relacionadas con tu consulta:\n"
                    f"{productos_info}\n\n"
                    f"¿Te gustaría más información sobre alguno de estos productos?"
                )
            else:
                print("No se encontraron productos ni con términos ampliados.")
                respuesta = (
                    "Lo siento, no encontré productos específicos para tu consulta en nuestro catálogo. "
                    "Sin embargo, puedo ayudarte a explorar opciones generales o darte recomendaciones. "
                    "¿Quieres que busquemos algo más o te oriente de otra manera?"
                )

            # Enviar respuesta al cliente
            enviar_respuesta_whatsapp(numero_cliente, respuesta)
        else:
            print("No hay mensajes en la solicitud.")
        return {"status": "success"}
    except Exception as e:
        print("Error en el webhook:", e)
        return {"status": "error", "error": str(e)}


# Función para generar términos relacionados usando OpenAI
def generar_terminos_relacionados(texto_usuario):
    try:
        prompt = f"""
Eres un modelo avanzado de lenguaje natural. Analiza el siguiente texto para generar términos relacionados que puedan ayudar a buscar productos en un catálogo de ferretería:

Texto: "{texto_usuario}"

Por favor, devuelve una lista de términos relacionados, separados por comas.
"""
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Eres un generador de términos relacionados."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print("Error al generar términos relacionados:", response.text)
            return ""
    except Exception as e:
        print("Error al generar términos relacionados:", e)
        return ""


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
        else:
            print("Error al llamar a OpenAI:", response.text)
            return "Lo siento, no puedo responder en este momento."
    except Exception as e:
        print("Error al generar respuesta:", e)
        return "Ocurrió un error al procesar tu consulta."


# Función para extraer palabras clave usando OpenAI
def extraer_palabras_clave(texto_usuario):
    try:
        prompt = f"""
Eres un modelo avanzado de lenguaje natural. Tu tarea es analizar el siguiente texto y extraer las palabras clave más importantes para identificar productos en un catálogo:

Texto: "{texto_usuario}"

Por favor, devuelve solo las palabras clave relevantes separadas por comas.
"""
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Eres un analizador de palabras clave."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50
        }
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print("Error al extraer palabras clave:", response.text)
            return texto_usuario  # Si falla, usa el texto completo
    except Exception as e:
        print("Error al generar palabras clave:", e)
        return texto_usuario  # Si falla, usa el texto completo


def enviar_respuesta_whatsapp(numero_cliente, respuesta):
    try:
        whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_ID')  # Obtener el ID del teléfono de las variables de entorno
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
