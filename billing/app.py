import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from routes import bill_bp



app = Flask(__name__)

app.register_blueprint(bill_bp)

if __name__ == "__main__":
    app.run(debug=True)