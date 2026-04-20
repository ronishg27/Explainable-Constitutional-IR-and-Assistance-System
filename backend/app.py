import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from routes.api_routes import api_bp

# load env vars
load_dotenv(dotenv_path=".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
    
app = Flask(__name__)
# cors setup
CORS(app)

app.register_blueprint(api_bp)




if __name__ == "__main__":
    # NOTE: debug=True should only for development
    app.run(debug=True)