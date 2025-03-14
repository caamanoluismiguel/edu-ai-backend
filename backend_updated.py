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

# Get OpenAI API Key from Railway environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Ensure it's set in Railway's environment variables.")

openai.api_key = OPENAI_API_KEY

# Existing endpoints (Tutor, Lesson Plan, Quiz, Teaching Materials) here...

# New Image Generator API endpoint
@app.route('/image_generator', methods=['POST'])
def image_generator():
    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()
        level = data.get("level", "").strip()
        ratio = data.get("ratio", "").strip()
        style = data.get("style", "default").strip()

        if not topic or not level or not ratio:
            return jsonify({"error": "Please provide topic, level, and ratio."}), 400

        # Construct the prompt for image generation, ensuring no text overlay.
        prompt = (
            f"Generate an educational illustration for teaching {topic} to {level} students in a {ratio} format, "
            f"using a {style} style. The image should be visually appealing and informative, and must not contain any text overlay."
        )

        # Map the ratio to an allowed size
        if ratio.lower() == "square":
            size = "1024x1024"
        elif ratio.lower() == "landscape":
            size = "1792x1024"
        elif ratio.lower() == "portrait":
            size = "1024x1792"
        else:
            size = "1024x1024"  # Default to square if unrecognized

        # Call the image generation API (DALL·E via OpenAI)
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=size
        )

        image_url = response["data"][0]["url"]
        return jsonify({"image_url": image_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
