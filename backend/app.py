from flask import Flask, request, jsonify

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


    return jsonify({
        "query": query,
        "response": "Response placeholder.",
        "articles": "Articles placeholder."
        })


if __name__ == "__main__":
    app.run(debug=True)