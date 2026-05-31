import requests
import json

class LLMController:
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
    def load_model(self):
        # Ollama automatically loads the model into memory on the first request.
        # We query the tags endpoint to check if Ollama is running and auto-detect models.
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                if models:
                    available_names = [m.get("name") for m in models]
                    # Dynamic prioritization: Auto-detect and default to the fastest model downloaded
                    priorities = ["gemma2", "qwen2", "llama3"]
                    best_model = None
                    for priority in priorities:
                        for name in available_names:
                            if priority in name:
                                best_model = name
                                break
                        if best_model:
                            break
                            
                    if best_model:
                        self.model_name = best_model
                    else:
                        self.model_name = models[0].get("name")
                    return True, f"Connected to Ollama. Active model: {self.model_name}"
                return False, "Ollama is running, but no models were found. Run 'ollama run gemma2:2b' in your terminal."
            return False, "Ollama responded with an error."
        except requests.exceptions.RequestException:
            return False, "Could not connect to Ollama. Please make sure the Ollama app is installed and running."

    def generate_stream(self, prompt, max_tokens=256):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": max_tokens
            }
        }
        try:
            response = requests.post(self.api_url, json=payload, stream=True)
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode('utf-8'))
                    yield chunk.get("response", "")
        except Exception as e:
            yield f"\n[Ollama Error] {e}"
