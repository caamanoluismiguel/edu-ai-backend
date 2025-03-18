import os
import subprocess
import openai
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# youtube_transcript_api imports
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")
openai.api_key = OPENAI_API_KEY


###################################
# Existing Edvanta Tools Endpoints
###################################

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


# NEW: Image Generator API
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


# NEW: Expand Content API
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


###########################################
# TeachTube AI - New Endpoint
###########################################

# Helper functions for transcript retrieval
def extract_video_id(youtube_url: str) -> str:
    """
    Naive approach to parse out the video ID.
    Works for https://www.youtube.com/watch?v=XXXX and https://youtu.be/XXXX
    """
    if "youtube.com/watch?v=" in youtube_url:
        return youtube_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/")[1]
    return ""

def get_transcript_primary(video_id: str) -> str or None:
    """
    Attempt to retrieve transcript via youtube_transcript_api. Returns transcript or None.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # We try manual or auto-generated in English
        for transcript in transcript_list:
            # If it's either EN or auto-generated
            if transcript.language_code == "en" or transcript.is_generated:
                fetched = transcript.fetch()
                # Combine text
                return " ".join([x["text"] for x in fetched])
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logging.warning(f"Primary transcript retrieval failed: {e}")
    except Exception as e:
        logging.warning(f"Primary transcript unexpected error: {e}")
    return None

def get_transcript_fallback(youtube_url: str) -> str or None:
    """
    Fallback using yt-dlp: attempt to download .vtt, parse to text.
    """
    try:
        temp_filename = "temp_subs"
        command = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", "en",
            "--skip-download",
            "--output", temp_filename,
            youtube_url
        ]
        subprocess.run(command, check=True)

        vtt_file = f"{temp_filename}.en.vtt"
        if os.path.exists(vtt_file):
            with open(vtt_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Minimal parsing
            transcript_text = []
            for line in lines:
                line = line.strip()
                if "-->" in line or not line:
                    continue
                transcript_text.append(line)
            # Clean up after ourselves
            os.remove(vtt_file)
            return " ".join(transcript_text)
    except Exception as e:
        logging.warning(f"Fallback transcript retrieval failed: {e}")
    return None

@app.route('/teachtube_ai', methods=['POST'])
def teachtube_ai():
    """
    Accepts JSON {"youtube_url": "..."} and returns a JSON with:
    {
      "study_guide": {...},
      "lesson_plan": {...},
      "quiz": [...],
      "worksheet": [...],
      "ppt_outline": [...]
    }
    """
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "")
        if not youtube_url:
            return jsonify({"error": "Missing 'youtube_url' parameter."}), 400

        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({"error": "Invalid or unrecognized YouTube URL."}), 400

        # 1) Attempt primary transcript
        transcript = get_transcript_primary(video_id)
        if not transcript:
            # fallback
            transcript = get_transcript_fallback(youtube_url)

        if not transcript:
            return jsonify({"error": "No transcript found via primary or fallback methods."}), 404

        # 2) Create forced JSON prompt
        prompt = f"""
You are a teaching assistant AI. You have a transcript of a YouTube video:

\"\"\"{transcript}\"\"\"

Generate the following sections in a single JSON response with these keys:
1) study_guide
2) lesson_plan
3) quiz
4) worksheet
5) ppt_outline

Each key must be present. Below is the desired JSON structure (example). Always fill all sections:

{{
  "study_guide": {{
    "summary": "...",
    "discussion_questions": ["..."],
    "vocabulary": ["..."]
  }},
  "lesson_plan": {{
    "objectives": ["..."],
    "introduction": "...",
    "activities": ["..."],
    "assessment": "...",
    "conclusion": "..."
  }},
  "quiz": [
    {{
      "question": "...",
      "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "B"
    }},
    ...
  ],
  "worksheet": [...],
  "ppt_outline": [
    {{
      "slide_title": "...",
      "bullet_points": ["...", "..."]
    }}
  ]
}}

Remember:
- study_guide: summary, discussion questions, vocabulary
- lesson_plan: objectives, introduction, activities, assessment, conclusion
- quiz: at least 5 questions, 4 choices each, with correct_answer
- worksheet: at least 3 exercises
- ppt_outline: at least 3 slides with bullet points

Return valid JSON ONLY, without extra commentary.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful teaching assistant AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        gpt_output = response["choices"][0]["message"]["content"].strip()

        # 3) Attempt to parse as JSON
        import json
        try:
            final_json = json.loads(gpt_output)
            return jsonify(final_json)
        except json.JSONDecodeError:
            logging.error("Failed to parse GPT output as JSON.")
            return jsonify({
                "error": "GPT output was not valid JSON.",
                "raw_output": gpt_output
            }), 500

    except Exception as e:
        logging.error(f"TeachTube AI error: {e}")
        return jsonify({"error": str(e)}), 500


###################################
# Main
###################################
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
