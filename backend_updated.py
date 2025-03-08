import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get OpenAI API Key from Railway environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")

openai.api_key = OPENAI_API_KEY

@app.route('/tutor_assistant', methods=['POST'])
def tutor_assistant():
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "Please provide a question for the AI Tutor."}), 400

        # AI prompt with default educational personality
        prompt = f'''
        You are an experienced education coach helping teachers improve their lessons, student engagement, and teaching strategies.
        Your role is to provide clear, structured, and detailed guidance to teachers.
        
        Teacher's Question: "{question}"
        
        Provide a well-structured response with actionable advice.
        '''

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful education expert AI."},
                      {"role": "user", "content": prompt}],
            temperature=0.7
        )

        ai_response = response["choices"][0]["message"]["content"]

        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
