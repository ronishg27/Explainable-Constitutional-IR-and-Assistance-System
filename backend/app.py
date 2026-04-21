import logging
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from config.db_connect import Database
from routes.api_routes import api_bp
from routes.auth_routes import auth_bp

# load env vars
load_dotenv(dotenv_path=".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
    
app = Flask(__name__)
# cors setup
CORS(app)

# db connection
db = Database()
DB_NAME = os.getenv("MONGO_DB_NAME", "ECIRAS")
HOST = os.getenv("MONGO_URI", "mongodb://localhost:27017")
db.connect(db_name=DB_NAME, host=HOST)  # Connect to the database when the app starts

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)




if __name__ == "__main__":
    # NOTE: debug=True should only for development
    app.run(debug=True)
    