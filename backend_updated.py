
import os
from flask import Flask, request, jsonify
import openai
from dotenv import load_dotenv
from flask_cors import CORS

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)  # Habilitar CORS completamente

# Obtener la clave de OpenAI desde el archivo .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.after_request
def add_cors_headers(response):
    """ Forzar encabezados CORS """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.route('/optimize_prompt', methods=['POST', 'OPTIONS'])
def optimize_prompt():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight OK"})
        return add_cors_headers(response)

    data = request.json
    prompt = data.get("prompt", "")

    if not OPENAI_API_KEY:
        return add_cors_headers(jsonify({"error": "API Key no configurada"})), 500

    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Mejora este prompt siguiendo la estructura IDEA."},
                      {"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )

        optimized_prompt = response["choices"][0]["message"]["content"].strip()
        return add_cors_headers(jsonify({"optimized_prompt": optimized_prompt}))

    except Exception as e:
        return add_cors_headers(jsonify({"error": str(e)})), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
