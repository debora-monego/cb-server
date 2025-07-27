from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({"message": "Login route works"})

@app.route('/api/auth/check-auth', methods=['GET'])
def check_auth():
    return jsonify({"message": "Check auth route works"})

if __name__ == '__main__':
    print("Starting simple Flask app...")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    app.run(debug=True, port=5000)