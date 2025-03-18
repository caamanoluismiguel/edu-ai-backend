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
CORS(app, resources={r"/*": {"origins": "*"}})

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")
openai.api_key = OPENAI_API_KEY

# -----------------------------
# Existing Endpoints (omitted for brevity)
# -----------------------------

@app.route('/teachtube_ai', methods=['POST'])
def teachtube_ai():
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "")
        if not youtube_url:
            return jsonify({"error": "Please provide a YouTube URL."}), 400

        # Extract the video ID using regex
        video_id_pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?].*)?"
        match = re.search(video_id_pattern, youtube_url)
        if match:
            video_id = match.group(1)
            logger.info(f"Extracted video ID: {video_id}")
        else:
            logger.error("Failed to extract video ID.")
            return jsonify({"error": "Invalid YouTube URL or unable to extract video ID."}), 400

        # Retrieve transcript using youtube_transcript_api with fallback
        transcript_list = None
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            logger.info("Transcript retrieved with get_transcript.")
        except Exception as primary_error:
            logger.warning(f"Primary transcript retrieval failed: {primary_error}")
            try:
                transcript_obj = YouTubeTranscriptApi.list_transcripts(video_id)
                try:
                    transcript_list = transcript_obj.find_transcript(['en']).fetch()
                    logger.info("Manual transcript retrieved for 'en'.")
                except Exception as manual_error:
                    logger.warning(f"Manual transcript retrieval failed: {manual_error}. Trying auto-generated transcripts.")
                    transcript_list = transcript_obj.find_generated_transcript(['en', 'en-US', 'en-GB']).fetch()
                    logger.info("Auto-generated transcript retrieved.")
            except Exception as fallback_error:
                logger.error(f"Fallback transcript retrieval failed: {fallback_error}")
                return jsonify({"error": f"Could not retrieve transcript: {fallback_error}"}), 400

        if not transcript_list:
            logger.error("Transcript list is empty after fallback.")
            return jsonify({"error": "Transcript could not be retrieved."}), 400

        transcript_text = " ".join([t["text"] for t in transcript_list])
        logger.info(f"Transcript text length: {len(transcript_text)} characters")

        # Build a simpler prompt that worked previously (it might produce incomplete results on first pass)
        prompt = f"""
You are an expert educational content generator. Using the transcript below from the YouTube video {youtube_url}, generate teaching materials including:
- a study guide,
- a lesson plan,
- a quiz,
- a worksheet, and
- a PowerPoint outline.

If some sections have insufficient detail, produce a minimal version for those sections.
Transcript:
---
{transcript_text}
---
Output the result in valid JSON with the following keys: study_guide, lesson_plan, quiz, worksheet, ppt_outline.
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

        try:
            output_json = json.loads(ai_output)
            logger.info("Parsed OpenAI response as JSON.")
        except Exception as parse_error:
            logger.error(f"JSON parsing error: {parse_error}")
            output_json = {"raw_output": ai_output, "error": f"JSON parsing error: {str(parse_error)}"}

        return jsonify(output_json)
    except Exception as e:
        logger.error(f"TeachTube AI endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
