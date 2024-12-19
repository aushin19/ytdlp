from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a folder for downloads if it doesn't exist
DOWNLOAD_FOLDER = "./downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def generate_unique_filename(title):
    """Generate a unique filename starting with the first word of the title and an alphanumeric identifier."""
    # Clean the title to remove invalid characters
    first_word = ''.join(c for c in title.split()[0] if c.isalnum()) if title else "video"
    unique_name = f"{first_word}_{uuid.uuid4().hex}"
    return os.path.join(DOWNLOAD_FOLDER, unique_name)

def download_video(url, output_format, audio_quality="192", video_quality="best"):
    """Download YouTube video in the specified format (mp4 or mp3)."""
    try:
        # First get video info
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            unique_filename = generate_unique_filename(title)

        # Set up options based on format
        options = {
            'outtmpl': f"{unique_filename}.%(ext)s",
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            },
        }

        if output_format == 'mp3':
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }],
            })
            final_filename = f"{unique_filename}.mp3"
        else:  # mp4
            if video_quality == 'best':
                format_str = 'bestvideo+bestaudio/best'
            else:
                format_str = f'bestvideo[height<={video_quality}]+bestaudio/best'
            
            options.update({
                'format': format_str,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })
            final_filename = f"{unique_filename}.mp4"

        logger.info(f"Starting download with options: {options}")
        
        with yt_dlp.YoutubeDL(options) as ydl:
            error_code = ydl.download([url])
            if error_code != 0:
                raise Exception(f"yt-dlp returned error code: {error_code}")

        if os.path.exists(final_filename):
            logger.info(f"Download successful: {final_filename}")
            return final_filename
        else:
            raise FileNotFoundError(f"Expected output file not found: {final_filename}")

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

@app.route('/api/download', methods=['POST'])
def download():
    """API endpoint to download YouTube video as MP4 or MP3."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        url = data.get('url')
        output_format = data.get('format', 'mp4').lower()
        audio_quality = str(data.get('audio_quality', '192'))
        video_quality = str(data.get('video_quality', 'best'))

        # Validate inputs
        if not url:
            return jsonify({"error": "You must provide a YouTube URL"}), 400

        if output_format not in ['mp4', 'mp3']:
            return jsonify({"error": "Invalid format. Supported formats are 'mp4' and 'mp3'"}), 400

        if output_format == 'mp3' and audio_quality not in ['128', '192', '320']:
            return jsonify({"error": "Invalid audio quality. Supported qualities are '128', '192', and '320'"}), 400

        if output_format == 'mp4' and video_quality not in ['144', '240', '360', '480', '720', '1080', 'best']:
            return jsonify({"error": "Invalid video quality. Supported qualities are '144', '240', '360', '480', '720', '1080', and 'best'"}), 400

        file_path = download_video(url, output_format, audio_quality, video_quality)

        if file_path and os.path.exists(file_path):
            return jsonify({
                "message": "Download complete",
                "file_path": file_path,
                "format": output_format,
                "quality": audio_quality if output_format == 'mp3' else video_quality
            })
        else:
            return jsonify({"error": "Download failed", "details": "Failed to create output file"}), 500

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({"error": "Server error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)