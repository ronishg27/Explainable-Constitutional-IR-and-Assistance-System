import os

from ollama import Client


def createOllamaClient()-> Client: 
  ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
  ollama_api_key = os.environ.get('OLLAMA_API_KEY') or ""

  headers = None
  if ollama_api_key.strip():
    headers = {"Authorization": f"Bearer {ollama_api_key.strip()}"}

  return Client(host=ollama_host, headers=headers)
