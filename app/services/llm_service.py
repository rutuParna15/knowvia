
import os
import requests

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:1.7b"
)

GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"


def generate_response(
    prompt: str,
    temperature: float = 0.2,
    num_predict: int = 512
) -> str:
    """
    Generate a response using a locally running Ollama model.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict
        }
    }

    try:
        response = requests.post(
            GENERATE_URL,
            json=payload,
            timeout=(10, 180)
        )

        response.raise_for_status()

        result = response.json()
        answer = result.get("response", "").strip()

        if not answer:
            raise RuntimeError("Ollama returned an empty response.")

        return answer

    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from exc

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Ollama request timed out."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Ollama returned an HTTP error: {exc.response.text}"
        ) from exc
