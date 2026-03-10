from flask import Flask
from routes import bill_bp


app = Flask(__name__, static_folder='static')

app.register_blueprint(bill_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)