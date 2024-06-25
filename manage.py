from flask import Flask, request, jsonify, send_from_directory
import instaloader
import re
import os
import shutil

app = Flask(__name__)

# Create an instance of Instaloader
L = instaloader.Instaloader()

# Function to extract shortcode from URL
def extract_shortcode(url):
    pattern = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel)/([^/?#&]+)")
    match = pattern.search(url)
    if match:
        return match.group(1)
    return url

@app.route('/download', methods=['POST'])
def download_instagram_post():
    data = request.json
    post_url = data.get('url', None)
    
    if post_url:
        try:
            shortcode = extract_shortcode(post_url)
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            # Create a directory for the shortcode if it doesn't exist
            target_dir = os.path.join(os.getcwd(), shortcode)
            os.makedirs(target_dir, exist_ok=True)
            # Change the download directory for Instaloader
            L.dirname_pattern = target_dir
            # Download post to the target directory
            L.download_post(post, target=shortcode)
            # Retrieve all filenames in the shortcode folder
            file_urls = []
            for filename in os.listdir(target_dir):
                if filename.endswith(('.jpg', '.mp4')):  # Filtering images and videos
                    download_url = f"http://{request.host}/{shortcode}/{filename}"
                    file_urls.append(download_url)
            result = {
                'url': post_url,
                'status': 'success',
                'shortcode': shortcode,
                'download_urls': file_urls
            }
        except instaloader.exceptions.InstaloaderException as e:
            result = {
                'url': post_url,
                'status': 'failed',
                'error': str(e)
            }
    else:
        result = {
            'status': 'failed',
            'error': 'No URL provided in request data'
        }
    
    return jsonify(result)

@app.route('/<shortcode>/<filename>', methods=['GET'])
def serve_file(shortcode, filename):
    directory = os.path.join(os.getcwd(), shortcode)
    return send_from_directory(directory, filename)

@app.route('/remove_folder', methods=['POST'])
def remove_folder():
    data = request.json
    shortcode = data.get('shortcode', None)
    
    if shortcode:
        try:
            # Construct path to folder using shortcode
            folder_path = os.path.join(os.getcwd(), shortcode)
            # Check if folder exists
            if os.path.exists(folder_path):
                # Remove the folder and its contents
                shutil.rmtree(folder_path)
                result = {
                    'status': 'success',
                    'message': f"Folder with shortcode {shortcode} removed successfully"
                }
            else:
                result = {
                    'status': 'failed',
                    'error': f"Folder with shortcode {shortcode} does not exist"
                }
        except Exception as e:
            result = {
                'status': 'failed',
                'error': f"Error removing folder: {str(e)}"
            }
    else:
        result = {
            'status': 'failed',
            'error': 'No shortcode provided in request data'
        }
    
    return jsonify(result)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', debug=False)
