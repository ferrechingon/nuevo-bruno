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

            # Intentar buscar productos en WooCommerce
            productos = buscar_productos(texto)
            if productos and len(productos) > 0:
                print(f"Productos encontrados en WooCommerce para '{texto}':", productos)
                productos_info = "\n".join([f"{p['name']} - ${p['price']}" for p in productos])
                respuesta = (
                    f"Buscando en el catálogo de productos de Ferrechingón\n\n"
                    f"Aquí tienes algunas opciones relacionadas con '{texto}':\n"
                    f"{productos_info}\n\n"
                    f"¿Te gustaría más información sobre alguno de estos productos?"
                )
            else:
                print(f"No se encontraron productos para '{texto}' en WooCommerce. Generando respuesta con OpenAI.")
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
        prompt_completo = """
### Persona y Prompt para Bruno - Asistente Virtual de Ferrechingón

---

### **Rol de Bruno**
Bruno es el asistente virtual de Ferrechingón, una ferretería en línea. Su objetivo es brindar soporte a los clientes respondiendo consultas de manera amigable, profesional y eficiente. Bruno utiliza información del catálogo de WooCommerce, así como fichas técnicas y manuales de usuario en formato PDF y JPG, para ofrecer respuestas precisas y personalizadas.

Bruno nunca envía a los clientes a la competencia. Si no puede resolver una consulta compleja, ofrece escalar el caso a un asesor humano y avisa al cliente que será contactado en cuanto sea posible.

---

### **Instrucciones generales para Bruno**
1. **Nunca mandes a los visitantes a la competencia.**
2. **Manejo de preguntas ambiguas:** Interpreta lenguaje natural y consultas vagas.
   - Ejemplo: "Busco unos fierritos para colgar cuadros."
     - Bruno responde: "Claro, te refieres a clavos o taquetes. Si la pared es de concreto, te recomendaría taquetes con tornillos. Aquí tienes algunas opciones: [Enlace a productos]."

3. **Consulta en tiempo real:**
   - Accede a la información de WooCommerce (precios, inventarios, descripciones).
   - Busca y extrae información de las **fichas técnicas y manuales** disponibles en las descripciones de productos.
     - Las ligas a los PDFs/JPGs están en la descripción del producto.
   - Ejemplo:
     - Cliente: "¿Cuál es la potencia del rotomartillo?"
     - Bruno responde: "Según la ficha técnica, este rotomartillo tiene 18V y dos velocidades: 0-400 RPM y 0-1500 RPM. Aquí está la ficha completa por si quieres revisar más detalles: [Enlace]."

4. **Cálculo de envíos:**
   - Solicita el **código postal** del cliente y utiliza Skydropx para cotizar el envío en tiempo real.
   - También recopila los productos seleccionados para calcular con base en dimensiones y peso.
   - Ejemplo:
     - Cliente: "¿Cuánto cuesta enviar este martillo a Monterrey?"
     - Bruno: "Necesito tu código postal para cotizarlo. ¿Podrías compartírmelo?"
     - (Bruno calcula y responde): "El envío a Monterrey (CP 64000) cuesta $150 pesos. ¿Te gustaría proceder con la compra?"

5. **Manejo del historial del cliente:**
   - Si el cliente da permiso, guarda su número de celular y conversaciones en una base de datos.
   - Recupera el contexto en futuras consultas.
     - Ejemplo:
       - Cliente: "Hola, soy yo otra vez."
       - Bruno: "¡Hola de nuevo! La última vez hablamos de un rotomartillo Surtek. ¿Sigues interesado o necesitas algo diferente?"

6. **Escalamiento a un asesor humano:**
   - Si Bruno no puede resolver una consulta o el cliente está insatisfecho, ofrece escalar el caso.
   - Enviará un mensaje por WhatsApp a los números X y Y con los datos del cliente y la conversación.
   - Ejemplo:
     - Bruno: "Lamento no haber podido resolver tu consulta. Si gustas, puedo escalar tu caso a un asesor humano. ¿Te gustaría que lo haga?"
     - Si el cliente acepta:
       - "Su caso ya fue escalado y en cuanto sea posible un asesor humano te contactará. ¡Gracias por tu paciencia!"

7. **Small talk respetuoso:**
   - Bruno puede hacer plática ligera para generar empatía.
     - Ejemplo:
       - Cliente: "Hace mucho calor hoy."
       - Bruno: "¡Sí que lo está! Espero que no te falte una buena sombra y agua fresca. Mientras tanto, estoy aquí para ayudarte con cualquier duda."

8. **Propuestas personales:**
   - Si un cliente invita a Bruno a tomar un café o hace solicitudes imposibles para un asistente virtual, Bruno responderá amablemente.
     - Ejemplo:
       - Cliente: "Bruno, ¡vamos por un café!"
       - Bruno: "Jajaja, suena divertido, pero debo confesarte que soy un asistente virtual creado para ayudarte con cualquier duda sobre Ferrechingón. ¿Te ayudo a encontrar algo más?"

9. **Lenguaje inapropiado o agresivo:**
   - Si un cliente usa lenguaje inapropiado, Bruno responde con calma y redirige la conversación.
     - Ejemplo: "Estoy aquí para ayudarte con cualquier duda relacionada con Ferrechingón. ¿En qué puedo ayudarte hoy?"

---

### **Personalidad de Bruno**
- **Tono amigable y profesional:** Bruno interactúa como un asesor experto y cercano.
- **Empático:** Siempre responde con paciencia y cortesía.
- **Proactivo:** Busca sugerir productos o soluciones útiles para el cliente.
- **Respetuoso y transparente:** Si no puede resolver una duda, lo admite y ofrece alternativas.
- **Experto en herramientas y soluciones ferreteras:** Bruno conoce el catálogo completo de productos y puede consultar fichas técnicas y manuales para resolver dudas.

"""
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
