from fastapi import FastAPI
import openai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "¡Hola, soy Bruno, listo para ayudarte!"}

@app.get("/test-openai/")
async def test_openai():
    try:
        # Agrega logs para depuración
        print("Probando la integración con OpenAI...")
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "Eres Bruno, un asistente virtual."},
                {"role": "user", "content": "¿Quién eres?"}
            ],
            "max_tokens": 50
        }
        print("Datos enviados a OpenAI:", data)

        # Solicitud a OpenAI
        response = openai.ChatCompletion.create(
            model=data["model"],
            messages=data["messages"],
            max_tokens=data["max_tokens"]
        )

        # Log de la respuesta de OpenAI
        print("Respuesta de OpenAI:", response)
        return {"response": response['choices'][0]['message']['content']}
    except Exception as e:
        print(f"Error al conectar con OpenAI: {str(e)}")
        return {"error": str(e)}
