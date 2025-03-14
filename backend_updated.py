import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")
openai.api_key = OPENAI_API_KEY

# AI Tutor Assistant API
@app.route('/tutor_assistant', methods=['POST'])
def tutor_assistant():
    try:
        data = request.get_json()
        question = data.get("question", "")
        if not question:
            return jsonify({"error": "Please provide a question for the AI Tutor."}), 400

        prompt = f"""
You are an experienced education coach helping teachers improve their lessons and strategies.
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
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lesson Plan Generator API
@app.route('/lesson_plan', methods=['POST'])
def lesson_plan():
    try:
        data = request.get_json()
        subject = data.get("subject", "")
        grade_level = data.get("grade_level", "")
        learning_goals = data.get("learning_goals", "")
        if not subject or not grade_level or not learning_goals:
            return jsonify({"error": "Please provide subject, grade level, and learning goals."}), 400

        prompt = f"""
You are an expert educator creating structured lesson plans for teachers.
Subject: {subject}
Grade Level: {grade_level}
Learning Goals: {learning_goals}
Generate a detailed lesson plan with:
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
        topic = data.get("topic", "")
        question_type = data.get("question_type", "multiple-choice")
        if not topic:
            return jsonify({"error": "Please provide a quiz topic."}), 400

        prompt = f"""
You are an expert quiz creator for educational purposes.
Topic: {topic}
Question Type: {question_type}
Generate a structured quiz with at least 5 questions. If multiple-choice, include four options per question and mark the correct answer.
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
        topic = data.get("topic", "")
        material_type = data.get("material_type", "study_guide")
        if not topic:
            return jsonify({"error": "Please provide a topic."}), 400

        prompt = f"""
You are an expert in creating educational materials for teachers.
Topic: {topic}
Material Type: {material_type}
Generate detailed and structured content based on the selected material type.
For PowerPoint slides, outline key slides. For worksheets, provide structured questions.
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

# NEW: Expand Content API
@app.route('/expand_content', methods=['POST'])
def expand_content():
    try:
        data = request.get_json()
        current_content = data.get("content", "")
        tool = data.get("tool", "")
        if not current_content:
            return jsonify({"error": "No content provided for expansion."}), 400

        # Create a prompt to expand the given content
        prompt = f"""
You are an expert in educational content enhancement.
Expand and elaborate on the following content to provide additional detail and insights. Ensure the response is well-structured and actionable.
Content: {current_content}
Tool: {tool}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert content expander."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        expanded_content = response["choices"][0]["message"]["content"]
        return jsonify({"expanded_content": expanded_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
