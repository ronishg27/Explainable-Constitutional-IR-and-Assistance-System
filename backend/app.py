from flask import Flask, request, jsonify
from src.llm.rag_workflow import RAGWorkflow
import logging
from flask_cors import CORS
from dotenv import load_dotenv

# load env vars
load_dotenv(dotenv_path=".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
    
app = Flask(__name__)
# cors setup
CORS(app)

# initialize workflow
workflow = RAGWorkflow()

# Check connection to Ollama at startup
_, status_message = workflow.check_ollama_connection()
logging.info(f"Ollama connection status: {status_message}")

@app.route("/api/v1", methods=["GET"])
def home():
    return jsonify({
            "message": "Welcome to the API!",
            "endpoints": {
                "/api/v1/health": "Check the health of the API.",
                "/api/v1/ask": "Submit a query to get a response."
            },
            'version': '1.0.0',
        })


@app.route("/api/v1/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/v1/ask", methods=["POST"])
def ask():
    
    # validate JSON
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Expected application/json."}), 400
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload."}), 400
    
    query = data.get("query")
    
    # validate query
    if not query:
        return jsonify({"error": "Query is required."}), 400
    
    if not isinstance(query, str):
        return jsonify({"error": "Query must be a string."}), 400
    
    if len(query) > 500:
        return jsonify({"error": "Query is too long. Maximum length is 500 characters."}), 400
    
    
    try:
        is_connected, status_message = workflow.check_ollama_connection()
        if not is_connected:
            logging.warning(f"Ollama unavailable during /ask: {status_message}")
            return jsonify({"error": "Ollama service is unavailable."}), 503
    
        result = workflow.ask(query, stream=False)
        return jsonify({
            "query": query,
            "response": result.get('answer'),
            "articles": result.get('retrieved_articles', [])
        })
        
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return jsonify({"error": "An error occurred while processing the query."}), 500




if __name__ == "__main__":
    # NOTE: debug=True should only for development
    app.run(debug=True)