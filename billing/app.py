from flask import Flask
from flask_cors import CORS
from routes import bill_bp


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(bill_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)