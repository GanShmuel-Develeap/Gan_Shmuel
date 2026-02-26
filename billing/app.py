import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from routes import bill_bp



app = Flask(__name__)

# DATABASE_URL = "mysql+pymysql://root:password@db/billdb"
DATABASE_URL = os.getenv('DATABASE_URL')

# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# # --- example ---
# @app.route('/getData/<name>')
# def add_user(name):
#     # Use db.session for managed transactions
    # query = text("INSERT INTO Provider (name) VALUES (:name)")
    # db.session.execute(query, {"name": name})
    
#     # Must commit to save changes to MySQL
    # db.session.commit()
    # return f"User {name} added!"


#     query = text("SELECT * FROM Provider")
#     result = db.session.execute(query)
    
#     # Fetch all rows and convert them to something readable (like a list of strings)
#     providers = [str(row) for row in result]
    
#     # If you were actually inserting data, you'd commit BEFORE returning
#     # db.session.commit() 
    
#     return f"Providers: {', '.join(providers)}"

app.register_blueprint(bill_bp)

if __name__ == "__main__":
    app.run(debug=True)