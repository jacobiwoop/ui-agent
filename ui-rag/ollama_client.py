"""
Ollama Client — gère les appels à Ollama/Qwen avec streaming et feedback.
"""

import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3.5:cloud"


def _call_ollama(messages: list, model: str, stream: bool = True) -> dict | str:
    """Appel bas niveau à l'API Ollama."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    full_response = ""
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if stream:
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            print(token, end="", flush=True)
                            full_response += token
                        if chunk.get("done"):
                            print()  # newline final
                            break
                    except json.JSONDecodeError:
                        continue
            else:
                data = json.loads(resp.read().decode("utf-8"))
                full_response = data.get("message", {}).get("content", "")

    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Impossible de contacter Ollama sur {OLLAMA_URL}\n"
            f"Vérifie que Ollama tourne : ollama serve\n"
            f"Erreur: {e}"
        )

    return full_response


def _parse_json_response(raw: str) -> dict:
    """Extrait et parse le JSON depuis la réponse brute du modèle.
    Gère le thinking mode de Qwen3 (<think>...</think>).
    """
    import re
    raw = raw.strip()

    if not raw:
        return {"error": "Réponse vide du modèle", "raw": ""}

    # Supprime le bloc <think>...</think> de Qwen3
    if "<think>" in raw:
        think_end = raw.rfind("</think>")
        if think_end != -1:
            raw = raw[think_end + len("</think>"):].strip()

    # Cas 1 : JSON pur
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Cas 2 : JSON dans un bloc markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Cas 3 : Cherche le premier { ... } valide (compte les accolades)
    brace_start = raw.find("{")
    if brace_start != -1:
        depth = 0
        for i, ch in enumerate(raw[brace_start:], brace_start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[brace_start:i + 1])
                    except json.JSONDecodeError:
                        break

    return {"error": "Impossible de parser la réponse JSON", "raw": raw[:800]}


def get_design_direction(messages: list, model: str = DEFAULT_MODEL) -> dict:
    """
    Appelle Ollama et retourne la direction design parsée.
    
    Args:
        messages: liste de messages au format Ollama
        model: nom du modèle Ollama à utiliser
    
    Returns:
        dict: direction design structurée
    """
    print(f"\n🤖 Qwen réfléchit", end="", flush=True)
    print("...\n")

    raw = _call_ollama(messages, model, stream=True)
    direction = _parse_json_response(raw)

    return direction


def check_ollama_available(model: str = DEFAULT_MODEL) -> bool:
    """Vérifie qu'Ollama est disponible et que le modèle existe."""
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            # Match exact OU par nom de base (avant le ":")
            model_base = model.split(":")[0]
            return any(
                m == model or m.split(":")[0] == model_base
                for m in models
            )
    except Exception:
        return False


def list_available_models() -> list:
    """Liste les modèles disponibles sur Ollama."""
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []