import os

from ollama import Client


def createOllamaClient()-> Client: 
  ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
  ollama_api_key = os.environ.get('OLLAMA_API_KEY') or ""

  headers = None
  if ollama_api_key.strip():
    headers = {"Authorization": f"Bearer {ollama_api_key.strip()}"}

  return Client(host=ollama_host, headers=headers)

def main() -> None:
  client = createOllamaClient()

  messages = [
    {
      "role": "user",
      "content": "What color is the sky? ",
    },
  ]

  try:
    for part in client.chat("gpt-oss:120b-cloud", messages=messages, stream=True):
      print(part.message.content, end="", flush=True)
    print()
  except Exception as exc:
    raise SystemExit(
      "Could not connect to Ollama. Start the Ollama server or set OLLAMA_HOST "
      "to the correct endpoint before running this script."
    ) from exc


if __name__ == "__main__":
  main()