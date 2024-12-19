from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = "./downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


def download_video(url, output_format, quality='192'):
    """Download YouTube video in the specified format (mp4 or mp3)."""
    options = {
        'format': 'bestvideo+bestaudio/best' if output_format == 'mp4' else 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }

    if output_format == 'mp3':
        options['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,  # Accept user-defined quality
            }
        ]

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if output_format == 'mp3':
                file_path = file_path.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return file_path
    except Exception as e:
        return str(e)


@app.route('/api/download/mp4', methods=['POST'])
def download_mp4():
    """API endpoint to download YouTube video as MP4."""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "You must provide a YouTube URL."}), 400

    file_path = download_video(url, 'mp4')
    if os.path.exists(file_path):
        return jsonify({"message": "Download complete", "file_path": file_path})
    else:
        return jsonify({"error": "Download failed", "details": file_path}), 500


@app.route('/api/download/mp3', methods=['POST'])
def download_mp3():
    """API endpoint to download YouTube video as MP3 with a specified quality."""
    data = request.json
    url = data.get('url')
    quality = data.get('quality', '192')

    if not url:
        return jsonify({"error": "You must provide a YouTube URL."}), 400

    file_path = download_video(url, 'mp3', quality)
    if os.path.exists(file_path):
        return jsonify({"message": "Download complete", "file_path": file_path})
    else:
        return jsonify({"error": "Download failed", "details": file_path}), 500


if __name__ == '__main__':
    app.run(debug=True)