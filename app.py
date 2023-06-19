from flask import Flask, request, jsonify
import string
import random
import datetime
import sqlite3
import urllib.parse


app = Flask(__name__)
url_mapping = {}
access_tokens = set()

def generate_short_url():
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(characters) for _ in range(6))
    return short_url

def is_valid_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def execute_query(query, params=None):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

@app.route('/shorten', methods=['POST'])
def shorten_url():
    if 'Authorization' not in request.headers:
        return jsonify({'error': 'Unauthorized'}), 401

    access_token = request.headers['Authorization']
    if access_token not in access_tokens:
        return jsonify({'error': 'Invalid access token'}), 401

    data = request.get_json()
    if 'url' not in data:
        return jsonify({'error': 'URL not provided'}), 400

    long_url = data['url']
    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL'}), 400

    short_url = generate_short_url()
    full_short_url = request.base_url + '/' + short_url  # Inclui a rota completa na URL encurtada

    query = "INSERT INTO urls (short_url, long_url) VALUES (?, ?)"
    params = (short_url, long_url)
    execute_query(query, params)

    return jsonify({'short_url': full_short_url}), 201  # Retorna a URL encurtada com a rota completa

@app.route('/shorten/custom', methods=['POST'])
def shorten_custom_url():
    if 'Authorization' not in request.headers:
        return jsonify({'error': 'Unauthorized'}), 401

    access_token = request.headers['Authorization']
    if access_token not in access_tokens:
        return jsonify({'error': 'Invalid access token'}), 401

    data = request.get_json()
    if 'url' not in data or 'custom_slug' not in data:
        return jsonify({'error': 'URL or custom slug not provided'}), 400

    long_url = data['url']
    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL'}), 400

    custom_slug = data['custom_slug']
    query = "SELECT * FROM urls WHERE short_url = ?"
    params = (custom_slug,)
    result = execute_query(query, params)
    if result:
        return jsonify({'error': 'Custom slug already in use'}), 409

    query = "INSERT INTO urls (short_url, long_url) VALUES (?, ?)"
    params = (custom_slug, long_url)
    execute_query(query, params)

    return jsonify({'short_url': custom_slug}), 201

@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    query = "SELECT * FROM urls WHERE short_url = ?"
    params = (short_url,)
    result = execute_query(query, params)
    if result:
        url_info = result[0]
        if url_info['expires_at'] is not None and url_info['expires_at'] < datetime.datetime.now():
            return jsonify({'error': 'Expired short URL'}), 410

        long_url = url_info['long_url']
        return jsonify({'long_url': long_url}), 301
    else:
        return jsonify({'error': 'Invalid short URL'}), 404

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    if 'access_token' not in data:
        return jsonify({'error': 'Access token not provided'}), 400

    access_token = data['access_token']
    # Realize a autenticação adequada, por exemplo,
    if access_token == 'YOUR_SECRET_ACCESS_TOKEN':
        access_tokens.add(access_token)
        return jsonify({'message': 'Authentication successful'}), 200
    else:
        return jsonify({'error': 'Invalid access token'}), 401

if __name__ == '__main__':
    app.run(debug=True)
