from flask import Flask, request, redirect
import requests

app = Flask(__name__)

@app.route('/')
@app.route('/<path:subpath>')
def handle_request(subpath=None):
    tera_url = request.args.get('url') or f"https://terafileshare.com/s/{subpath}"
    
    if not tera_url:
        return {"usage": "Add ?url=TERABOX_URL or /TERABOX_ID"}, 400
    
    api_url = f"https://terabox-dl.vercel.app/api?url={requests.utils.quote(tera_url)}"
    
    try:
        response = requests.get(api_url).json()
        if 'direct_link' in response:
            return redirect(response['direct_link'])
        return response
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run()
