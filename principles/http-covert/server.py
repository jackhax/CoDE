from flask import Flask, jsonify, request

app = Flask(__name__)

# Basic route for testing
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Simple Flask HTTP Server!", 200

# Example API endpoint that returns a JSON response
@app.route('/CoDE/http', methods=['GET'])
def get_data():
    print(dict(request.headers)['X-Csrf-Token'])
    data = {"message": "OK"}
    return jsonify(data), 200

app.run(host='127.0.0.1', port=5000)