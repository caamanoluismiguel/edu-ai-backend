import os
import openai
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
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

def get_video_id(youtube_url):
    """Extracts the video ID from a YouTube URL."""
    if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(youtube_url, download=False)
                return info_dict.get("id", None)
            except Exception as e:
                print("Error extracting video ID:", str(e))
    return None

def fetch_transcript(video_id):
    """Fetches transcript for a given YouTube video ID."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
        return transcript_text
    except Exception as e:
        print("Error fetching transcript:", str(e))
        return None

@app.route('/teachtube', methods=['POST'])
def teachtube():
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
Given the following transcript, generate the following teaching materials:
1. **Study Guide** (summary, key vocabulary, discussion questions)
2. **Lesson Plan** (objectives, introduction, activities, assessment, conclusion)
3. **Quiz** (5+ multiple-choice questions)
4. **Worksheet** (3+ exercises)
5. **PowerPoint Outline** (3+ slides with bullet points)

Transcript:
{transcript_text}
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that generates educational content from YouTube videos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        ai_response = response["choices"][0]["message"]["content"]
        return jsonify({"teachtube_output": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
