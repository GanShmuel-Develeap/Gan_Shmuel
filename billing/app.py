from flask import Flask
from routes import bill_bp

app = Flask(__name__)

app.register_blueprint(bill_bp)

if __name__ == "__main__":
    app.run(debug=True)