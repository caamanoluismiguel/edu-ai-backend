
import os
from flask import Flask, request, jsonify
import openai
from dotenv import load_dotenv
from flask_cors import CORS

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Permitir todas las solicitudes CORS

# Obtener la clave de OpenAI desde el archivo .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route('/optimize_prompt', methods=['POST'])
def optimize_prompt():
    data = request.json
    prompt = data.get("prompt", "")

    if not OPENAI_API_KEY:
        return jsonify({"error": "API Key no configurada"}), 500

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
        return jsonify({"optimized_prompt": optimized_prompt})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
