import os
import re
import json
import logging
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Tutor Assistant error: {str(e)}")
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
        logger.error(f"Lesson Plan error: {str(e)}")
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
Generate a structured quiz with at least 5 questions. For each question, include:
- "question": The question text,
- "options": An array of 4 options,
- "correct_answer": The correct option.
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
        logger.error(f"Quiz Creator error: {str(e)}")
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
        logger.error(f"Teaching Materials error: {str(e)}")
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
        logger.error(f"Image Generator error: {str(e)}")
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
        logger.error(f"Expand Content error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# -----------------------------
# New: TeachTube AI Endpoint with Enhanced Prompt and Logging
# -----------------------------
@app.route('/teachtube_ai', methods=['POST'])
def teachtube_ai():
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "")
        if not youtube_url:
            return jsonify({"error": "Please provide a YouTube URL."}), 400

        # Extract video ID
        video_id_pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?].*)?"
        match = re.search(video_id_pattern, youtube_url)
        if match:
            video_id = match.group(1)
            logger.info(f"Extracted video ID: {video_id}")
        else:
            logger.error("Failed to extract video ID.")
            return jsonify({"error": "Invalid YouTube URL or unable to extract video ID."}), 400

        # Retrieve transcript with logging
        transcript_list = None
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            logger.info("Successfully retrieved transcript using get_transcript with languages=['en'].")
        except Exception as primary_error:
            logger.warning(f"Primary transcript retrieval failed: {primary_error}")
            try:
                transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id)
                logger.info("Transcript list retrieved. Attempting to get manual transcript for 'en'.")
                try:
                    transcript_list = transcript_obj.find_transcript(['en']).fetch()
                    logger.info("Successfully retrieved manual transcript for 'en'.")
                except Exception as manual_error:
                    logger.warning(f"Manual transcript retrieval failed: {manual_error}. Trying auto-generated transcripts.")
                    transcript_list = transcript_obj.find_generated_transcript(['en', 'en-US', 'en-GB']).fetch()
                    logger.info("Successfully retrieved auto-generated transcript.")
            except Exception as fallback_error:
                logger.error(f"Fallback transcript retrieval failed: {fallback_error}")
                return jsonify({"error": f"Could not retrieve transcript: {fallback_error}"}), 400

        if not transcript_list:
            logger.error("Transcript list is empty after fallback attempts.")
            return jsonify({"error": "Transcript could not be retrieved."}), 400

        transcript_text = " ".join([t["text"] for t in transcript_list])
        logger.info(f"Transcript text length: {len(transcript_text)} characters")

        # Enhanced prompt with strict instructions
        prompt = f"""
You are an expert educational content generator. Based on the transcript provided from the YouTube video {youtube_url}, generate comprehensive teaching materials. You must produce all of the following sections in valid JSON format, and you must include every section even if the transcript lacks some details. If necessary, invent plausible content to satisfy the requirements. Do not omit any section.

Required JSON keys:
1. "study_guide": An object with:
    - "summary": A concise summary of the video.
    - "discussion_questions": An array of 3 to 5 discussion questions.
    - "vocabulary": An array of key vocabulary terms.
2. "lesson_plan": An object with:
    - "objectives": An array of at least 3 objectives.
    - "introduction": A brief introduction.
    - "activities": An array of at least 3 activities.
    - "assessments": An array of assessment methods.
    - "conclusion": A brief conclusion.
3. "quiz": An array of at least 5 quiz questions. Each question must include:
    - "question": The question text.
    - "options": An array of 4 options.
    - "correct_answer": The correct option.
4. "worksheet": An array of at least 3 open-ended or fill-in-the-blank exercises.
5. "ppt_outline": An object with:
    - "slide_titles": An array of at least 3 slide titles.
    - "bullet_points": An array where each element is an array of bullet points for the corresponding slide.

Transcript:
---
{transcript_text}
---
Output strictly in valid JSON with exactly these keys: study_guide, lesson_plan, quiz, worksheet, ppt_outline.
"""
        logger.info("Sending prompt to OpenAI.")
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
        logger.info("Received response from OpenAI.")

        # Attempt to parse the AI output as JSON
        try:
            output_json = json.loads(ai_output)
            logger.info("Successfully parsed OpenAI response as JSON.")
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {parse_error}")
            output_json = {"raw_output": ai_output, "error": f"JSON parsing error: {str(parse_error)}"}
        
        return jsonify(output_json)
    except Exception as e:
        logger.error(f"TeachTube AI endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
