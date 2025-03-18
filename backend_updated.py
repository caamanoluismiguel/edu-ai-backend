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
            temperature=0.7,
            max_tokens=1500
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
            temperature=0.7,
            max_tokens=1500
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
            temperature=0.7,
            max_tokens=1500
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
            temperature=0.7,
            max_tokens=1500
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
            temperature=0.7,
            max_tokens=1500
        )
        expanded_content = response["choices"][0]["message"]["content"]
        return jsonify({"expanded_content": expanded_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# New: TeachTube AI Endpoint with Enhanced Prompt
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

        # Retrieve transcript explicitly requesting English language with enhanced fallback
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except Exception as e:
            try:
                transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id)
                # First try to fetch the manually provided transcript
                try:
                    transcript_list = transcript_obj.find_transcript(['en']).fetch()
                except Exception as manual_e:
                    # Fallback to auto-generated transcripts using common English variants
                    transcript_list = transcript_obj.find_generated_transcript(['en', 'en-US', 'en-GB']).fetch()
            except Exception as inner_e:
                return jsonify({"error": f"Could not retrieve transcript: {str(inner_e)}"}), 400

        transcript_text = " ".join([t["text"] for t in transcript_list])
        
        # Improved prompt to force all sections with minimum requirements
        prompt = f"""
You are an expert educational content generator. Using the transcript provided below from the YouTube video {youtube_url}, generate comprehensive teaching materials. You must always produce the following sections in valid JSON format, even if the transcript does not have enough details—if necessary, create plausible, inferred content.

1. "study_guide": {{
      "summary": A concise summary of the video content,
      "discussion_questions": An array of 3 to 5 discussion questions,
      "vocabulary": An array of key vocabulary terms.
   }},
2. "lesson_plan": {{
      "objectives": An array of at least 3 objectives,
      "introduction": A brief introduction,
      "activities": An array of at least 3 activities,
      "assessments": An array of assessment methods (e.g., quiz, presentation),
      "conclusion": A brief conclusion.
   }},
3. "quiz": An array of at least 5 quiz questions. For each question, include:
      - "question": The question text,
      - "options": An array of 4 options,
      - "correct_answer": The correct option.
4. "worksheet": An array of at least 3 open-ended or fill-in-the-blank exercises.
5. "ppt_outline": {{
      "slide_titles": An array of at least 3 slide titles,
      "bullet_points": An array where each element is an array of bullet points corresponding to each slide.
   }}

Transcript:
---
{transcript_text}
---
Output strictly in valid JSON.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert educational content generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        ai_output = response["choices"][0]["message"]["content"]
        
        # Attempt to parse the AI output as JSON
        try:
            output_json = json.loads(ai_output)
        except Exception as parse_error:
            output_json = {"raw_output": ai_output, "error": f"JSON parsing error: {str(parse_error)}"}
        
        return jsonify(output_json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
