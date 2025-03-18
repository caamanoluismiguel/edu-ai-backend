import os
import subprocess
import openai
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

load_dotenv()

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")
openai.api_key = OPENAI_API_KEY

#############################################
# HELPER FUNCTIONS FOR TEACHTUBE AI
#############################################

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
    Attempt to retrieve an English transcript via youtube_transcript_api.
    Tries multiple language codes (en, en-US, en-GB) and auto-generated tracks.
    Returns transcript as a single string or None if not found.
    """
    try:
        logging.info(f"Trying primary transcript with youtube_transcript_api for video_id={video_id}")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try a set of English variants
        possible_lang_codes = ["en", "en-US", "en-GB", "en-AU"]

        for transcript in transcript_list:
            lang = transcript.language_code
            logging.info(f"Found transcript track: {lang}, generated={transcript.is_generated}")
            # If it's one of our English variants or an auto-generated track in English
            if lang in possible_lang_codes or transcript.is_generated:
                # Attempt to fetch
                fetched = transcript.fetch()
                combined_text = " ".join([x["text"] for x in fetched])
                if combined_text.strip():
                    return combined_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logging.warning(f"Primary transcript retrieval failed: {e}")
    except Exception as e:
        logging.warning(f"Primary transcript unexpected error: {e}")
    return None

def get_transcript_fallback(youtube_url: str) -> str or None:
    """
    Fallback using yt-dlp: attempt to download English auto-sub as a .vtt file, parse to text.
    """
    try:
        logging.info(f"Trying fallback transcript with yt-dlp for url={youtube_url}")

        temp_filename = "temp_subs"
        # Use wildcards for sub-langs in case it's en, en-US, en-GB, etc.
        command = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-langs", "en.*",  # Instead of just en
            "--skip-download",
            "--output", temp_filename,
            youtube_url
        ]
        subprocess.run(command, check=True)

        # Since we used "en.*", the actual file might be temp_subs.en.vtt or temp_subs.enUS.vtt, etc.
        import glob
        vtt_files = glob.glob("temp_subs*.vtt")

        if not vtt_files:
            logging.info("No .vtt file found from fallback method.")
            return None

        # We'll assume the first matching VTT
        vtt_file = vtt_files[0]
        logging.info(f"Found VTT file: {vtt_file}")

        with open(vtt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Minimal VTT parsing
        transcript_text = []
        for line in lines:
            line = line.strip()
            # Skip metadata/time lines
            if "-->" in line or not line:
                continue
            transcript_text.append(line)

        # Cleanup the file(s)
        for vf in vtt_files:
            try:
                os.remove(vf)
            except:
                pass

        combined_text = " ".join(transcript_text)
        return combined_text if combined_text.strip() else None
    except Exception as e:
        logging.warning(f"Fallback transcript retrieval failed: {e}")
    return None


#############################################
# TEACHTUBE AI ENDPOINT
#############################################

@app.route('/teachtube_ai', methods=['POST'])
def teachtube_ai():
    """
    Accepts JSON: { "youtube_url": "..." }
    Returns a JSON with keys: study_guide, lesson_plan, quiz, worksheet, ppt_outline
    or an error message if transcripts are unavailable.
    """
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "").strip()
        if not youtube_url:
            return jsonify({"error": "Missing 'youtube_url' parameter."}), 400

        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({"error": "Invalid or unrecognized YouTube URL."}), 400

        # 1) Primary attempt
        transcript = get_transcript_primary(video_id)
        if not transcript:
            # 2) Fallback attempt
            transcript = get_transcript_fallback(youtube_url)

        if not transcript:
            # Either the video truly has no English subtitles, or it's region-locked, etc.
            logging.error("No transcript found via primary or fallback methods.")
            return jsonify({"error": "No transcript found via primary or fallback methods."}), 404

        # 3) Prompt forcing GPT to return all sections in JSON
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

        import json
        try:
            final_json = json.loads(gpt_output)
            return jsonify(final_json)
        except json.JSONDecodeError:
            logging.error("Failed to parse GPT output as JSON.")
            return jsonify({"error": "GPT output was not valid JSON.", "raw_output": gpt_output}), 500

    except Exception as e:
        logging.error(f"TeachTube AI error: {e}")
        return jsonify({"error": str(e)}), 500


#############################################
# If you have other endpoints, keep them
#############################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
