import json
import re
import requests
from flask import Flask, request, render_template, send_file, after_this_request
import os

app = Flask(__name__)

# Function to read payloads from a text file
def read_payloads(file_path):
    with open(file_path, 'r') as file:
        payloads = file.read().splitlines()
    return payloads

# Function to insert the message into the payloads using heuristics
def personalize_payloads(payloads, message):
    pattern = re.compile(r"(alert|prompt|confirm)\((.*?)\)")
    personalized_payloads = []

    for payload in payloads:
        # Search for keywords and insert the message
        matches = pattern.findall(payload)
        if matches:
            for match in matches:
                old_text = f"{match[0]}({match[1]})"
                new_text = f"{match[0]}('{message}')"
                payload = payload.replace(old_text, new_text)
        personalized_payloads.append(payload)

    return personalized_payloads

# Function to download a payload list from a given URL
def download_payload_list(url):
    response = requests.get(url)
    response.raise_for_status()
    payloads = response.text.splitlines()
    return payloads

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/customize', methods=['POST'])
def customize():
    message = request.form['message']
    file_type = request.form['file_type']
    source = request.form['source']

    if source == 'upload':
        file = request.files['payload_file']
        payloads = file.read().decode('utf-8').splitlines()
    else:
        url = request.form['url']
        try:
            payloads = download_payload_list(url)
        except requests.RequestException as e:
            return f"Failed to download the payload list: {e}", 500

    formatted_payloads = personalize_payloads(payloads, message)

    filename = 'personalized_payloads.' + file_type
    with open(filename, 'w') as f:
        if file_type == 'txt':
            for payload in formatted_payloads:
                f.write(f"{payload}\n")
        elif file_type == 'json':
            json.dump(formatted_payloads, f, indent=4)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(filename)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)