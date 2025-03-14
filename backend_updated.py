import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_caching import Cache  # For caching responses

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure and initialize the cache (using SimpleCache for demonstration)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Get OpenAI API Key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in your environment variables.")

openai.api_key = OPENAI_API_KEY

# AI Tutor Assistant API with caching
@app.route('/tutor_assistant', methods=['POST'])
def tutor_assistant():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"error": "Please provide a question for the AI Tutor."}), 400

        # Use a cache key based on the lowercased question
        cache_key = f"tutor_{question.lower()}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return jsonify({"response": cached_response})

        prompt = f"""
You are an experienced education coach helping teachers improve their lessons, student engagement, and teaching strategies.
Teacher's Question: "{question}"
Provide a well-structured response with actionable advice.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful education expert AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        ai_response = response["choices"][0]["message"]["content"]
        cache.set(cache_key, ai_response)
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lesson Plan Generator API
@app.route('/lesson_plan', methods=['POST'])
def lesson_plan():
    try:
        data = request.get_json()
        subject = data.get("subject", "").strip()
        grade_level = data.get("grade_level", "").strip()
        learning_goals = data.get("learning_goals", "").strip()

        if not subject or not grade_level or not learning_goals:
            return jsonify({"error": "Please provide subject, grade level, and learning goals."}), 400

        prompt = f"""
You are an expert educator creating structured lesson plans for teachers.

Subject: {subject}
Grade Level: {grade_level}
Learning Goals: {learning_goals}

Generate a detailed lesson plan including:
- Lesson Objectives
- Introduction
- Activities
- Assessment Methods
- Conclusion
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a lesson plan generator AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        ai_response = response["choices"][0]["message"]["content"]
        return jsonify({"lesson_plan": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Quiz Creator API
@app.route('/quiz_creator', methods=['POST'])
def quiz_creator():
    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()
        question_type = data.get("question_type", "multiple-choice").strip()

        if not topic:
            return jsonify({"error": "Please provide a quiz topic."}), 400

        prompt = f"""
You are an expert quiz creator for educational purposes.

Topic: {topic}
Question Type: {question_type}

Generate a structured quiz with at least 5 questions based on the given topic.
If multiple-choice, provide four answer options per question with the correct answer marked.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI-based quiz generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        ai_response = response["choices"][0]["message"]["content"]
        return jsonify({"quiz": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Teaching Materials Generator API
@app.route('/teaching_materials', methods=['POST'])
def teaching_materials():
    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()
        material_type = data.get("material_type", "study_guide").strip()

        if not topic:
            return jsonify({"error": "Please provide a topic."}), 400

        prompt = f"""
You are an expert in creating educational materials for teachers.

Topic: {topic}
Material Type: {material_type}

Generate detailed and structured content for the selected material type.
If it's a PowerPoint slide, outline the key slides. If it's a worksheet, provide structured questions.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI-based teaching material generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        ai_response = response["choices"][0]["message"]["content"]
        return jsonify({"teaching_materials": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Simplified Image Generator API endpoint (new)
@app.route('/image_generator', methods=['POST'])
def image_generator():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"error": "Please provide a prompt."}), 400

        # Use a default size (square) for all images
        size = "1024x1024"

        # Refine the prompt to include descriptors for high quality and no text overlay.
        refined_prompt = (
            f"Generate an ultra-detailed, high-resolution, and vivid educational illustration based on the prompt: {prompt}. "
            f"The image should be visually appealing, in a realistic style, and must not contain any text overlay."
        )

        response = openai.Image.create(
            prompt=refined_prompt,
            n=1,
            size=size
        )
        image_url = response["data"][0]["url"]
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
