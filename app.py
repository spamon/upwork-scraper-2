from flask import Flask, request, send_file, jsonify, render_template
import instaloader
import requests
from bs4 import BeautifulSoup
from moviepy.editor import VideoFileClip
import os
import uuid
import shutil

app = Flask(__name__)

def download_instagram_video(url, download_path):
    L = instaloader.Instaloader()
    shortcode = url.split("/")[-2]
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=download_path)
        video_filename = next((filename for filename in os.listdir(download_path) if filename.endswith('.mp4')), None)
        if video_filename:
            cleaned_file = remove_metadata(os.path.join(download_path, video_filename))
            return cleaned_file
        else:
            raise Exception("No video file found.")
    except Exception as e:
        raise e

def download_tiktok_video(url, download_path):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        video_url = soup.find('video')['src']
        video_response = requests.get(video_url)
        video_path = os.path.join(download_path, 'tiktok_video.mp4')
        with open(video_path, 'wb') as f:
            f.write(video_response.content)
        cleaned_file = remove_metadata(video_path)
        return cleaned_file
    except Exception as e:
        raise e

def remove_metadata(filepath):
    try:
        video = VideoFileClip(filepath)
        clean_path = "clean_" + os.path.basename(filepath)
        video.write_videofile(clean_path, codec='libx264', audio_codec='aac')
        video.close()
        os.remove(filepath)
        return clean_path
    except Exception as e:
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    download_path = str(uuid.uuid4())
    os.mkdir(download_path)

    try:
        if "instagram.com" in url:
            file_path = download_instagram_video(url, download_path)
        elif "tiktok.com" in url:
            file_path = download_tiktok_video(url, download_path)
        else:
            return jsonify({"error": "Unsupported URL"}), 400
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(download_path):
            shutil.rmtree(download_path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
