from flask import Flask, request, jsonify

from src.llm.rag_workflow import RAGWorkflow

app = Flask(__name__)

@app.route("/api/v1")
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
    query = request.json.get("query")
    # place your logic to process the query here
    
    workflow = RAGWorkflow()

    is_connected, status_message = workflow.check_ollama_connection()

    print(status_message)
    if not is_connected:
        return jsonify({"error": "Failed to connect to Ollama."}), 500



    # Ask and get response (non-streaming for demo)
    result = workflow.ask(query, stream=False)



    return jsonify({
        "query": query,
        "response": result['answer'],
        "articles": result['retrieved_articles']
        })


if __name__ == "__main__":
    app.run(debug=True)