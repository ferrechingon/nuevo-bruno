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
        # Llamada sincrónica a la API de OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Usa GPT-4 si tienes acceso
            messages=[
                {"role": "system", "content": "Eres Bruno, un asistente virtual."},
                {"role": "user", "content": "¿Quién eres?"}
            ],
            max_tokens=50
        )
        return {"response": response['choices'][0]['message']['content']}
    except Exception as e:
        return {"error": str(e)}
