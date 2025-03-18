import os
import openai
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in your environment variables.")
openai.api_key = OPENAI_API_KEY

def get_video_id(youtube_url):
    """
    Extracts the video ID from a YouTube URL using yt-dlp.
    If the environment variable YOUTUBE_COOKIES_PATH is set, it uses the cookies file for authentication.
    """
    if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
        cookies_path = os.getenv("YOUTUBE_COOKIES_PATH")  # Path to your cookies file
        ydl_opts = {"quiet": True}
        if cookies_path:
            ydl_opts["cookiefile"] = cookies_path
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(youtube_url, download=False)
                return info_dict.get("id", None)
            except Exception as e:
                print("Error extracting video ID:", str(e))
    return None

def fetch_transcript(video_id):
    """
    Fetches transcript for a given YouTube video ID using YouTubeTranscriptApi.
    Attempts to fetch an English transcript. If a manually provided transcript is not available,
    it falls back to the auto-generated one.
    """
    try:
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            # Try to fetch a manually created transcript in English
            transcript = transcript_list.find_transcript(['en'])
        except NoTranscriptFound:
            # Fall back to auto-generated transcript in English
            transcript = transcript_list.find_generated_transcript(['en'])
        # Fetch the transcript and join the text
        transcript_data = transcript.fetch()
        transcript_text = " ".join([entry["text"] for entry in transcript_data])
        return transcript_text
    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as e:
        print("Transcript error:", str(e))
        return None
    except Exception as e:
        print("Unexpected error fetching transcript:", str(e))
        return None

@app.route('/teachtube', methods=['POST'])
def teachtube():
    """
    TeachTube AI endpoint:
    1. Extracts the video ID from the provided YouTube URL.
    2. Fetches the transcript using the improved transcript fetching method.
    3. Sends a detailed prompt to OpenAI GPT-4 for generating:
       - Study Guide
       - Lesson Plan
       - Quiz
       - Worksheet
       - PowerPoint Outline
    Each section is separated by a custom delimiter: [---SPLIT---]
    """
    try:
        data = request.get_json()
        youtube_url = data.get("youtube_url", "")
        if not youtube_url:
            return jsonify({"error": "Please provide a YouTube URL."}), 400

        video_id = get_video_id(youtube_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL or unable to extract video ID."}), 400

        transcript_text = fetch_transcript(video_id)
        if not transcript_text:
            return jsonify({"error": "Transcript not available for this video."}), 400

        prompt = f"""
You are an AI that extracts educational insights from YouTube videos. 
Below is the transcript for the video:

{transcript_text}

Please produce the following sections **in detail**, each separated by the delimiter: [---SPLIT---]

1. Study Guide
   - Write a robust summary (at least 2 paragraphs)
   - Provide 5 discussion questions
   - Provide 5 key vocabulary words with definitions

[---SPLIT---]

2. Lesson Plan
   - Objectives
   - Introduction
   - Activities (at least 2 activities)
   - Assessment (at least 1 method)
   - Conclusion

[---SPLIT---]

3. Quiz
   - Provide at least 5 multiple-choice questions
   - Each question has 4 options (A, B, C, D)
   - Mark the correct answer clearly

[---SPLIT---]

4. Worksheet
   - Provide at least 5 written exercises or tasks 
   - Make them interactive or reflective

[---SPLIT---]

5. PowerPoint Outline
   - Provide at least 5 slides with bullet points
   - Each slide should have a clear heading
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that generates educational content from YouTube videos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        ai_response = response["choices"][0]["message"]["content"]
        return jsonify({"teachtube_output": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
