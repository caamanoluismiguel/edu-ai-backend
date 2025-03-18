import os
import re
import json
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")
openai.api_key = OPENAI_API_KEY

# -----------------------------
# Existing Endpoints
# -----------------------------

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

@app.route('/image_generator', methods=['POST'])
def image_generator():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        if not prompt:
            return jsonify({"error": "Please provide an image prompt."}), 400

        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response["data"][0]["url"]
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/expand_content', methods=['POST'])
def expand_content():
    try:
        data = request.get_json()
        current_content = data.get("content", "")
        tool = data.get("tool", "")
        if not current_content:
            return jsonify({"error": "No content provided for expansion."}), 400

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

# -----------------------------
# New: TeachTube AI Endpoint
# -----------------------------
@app.route('/teachtube_ai', methods=['POST'])
def teachtube_ai():
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "")
        if not youtube_url:
            return jsonify({"error": "Please provide a YouTube URL."}), 400
        
        # Extract the video ID using regex with error checking
        video_id_pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?].*)?"
        match = re.search(video_id_pattern, youtube_url)
        if match:
            video_id = match.group(1)
        else:
            return jsonify({"error": "Invalid YouTube URL or unable to extract video ID."}), 400
        
        # Retrieve transcript using youtube_transcript_api
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            return jsonify({"error": f"Could not retrieve transcript: {str(e)}"}), 400
        
        transcript_text = " ".join([t["text"] for t in transcript_list])
        
        # Construct the prompt for generating teaching materials in JSON format
        prompt = f"""
You are an expert educational content generator. Generate comprehensive teaching materials from the provided YouTube transcript.
Transcript (from {youtube_url}):
---
{transcript_text}
---
Generate the following keys in valid JSON format:
- "study_guide": A concise summary, discussion questions, and vocabulary.
- "lesson_plan": Detailed lesson plan including objectives, introduction, activities, assessments, and conclusion.
- "quiz": A quiz with at least 5 questions. For multiple-choice questions, include 4 options and mark the correct answer.
- "worksheet": A set of exercises or worksheet questions.
- "ppt_outline": An outline for a PowerPoint presentation with slide titles and bullet points.
Output strictly in valid JSON.
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert educational content generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        ai_output = response["choices"][0]["message"]["content"]
        
        # Attempt to parse the AI output as JSON
        try:
            output_json = json.loads(ai_output)
        except Exception as parse_error:
            # If parsing fails, return the raw output for troubleshooting
            output_json = {"raw_output": ai_output, "error": f"JSON parsing error: {str(parse_error)}"}
        
        return jsonify(output_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
