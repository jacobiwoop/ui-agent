"""
rag_agent.py — Agent RAG avec function calling Ollama.
Qwen décide lui-même quelles recherches faire et combien.
"""

import json
import urllib.request
import urllib.error
from vector_store import get_store

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3.5:cloud"
MAX_ITERATIONS = 5  # sécurité anti-boucle infinie

# ── Définition des outils exposés à Qwen ─────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_uiux",
            "description": (
                "Recherche dans la base de connaissances UI/UX. "
                "Retourne les guidelines, styles, couleurs, typographies, "
                "patterns de landing page et règles de stack les plus pertinents. "
                "Appelle cette fonction autant de fois que nécessaire avec des "
                "requêtes différentes pour couvrir tous les aspects du projet."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Requête de recherche en anglais de préférence. "
                            "Ex: 'sport ecommerce bold dynamic', "
                            "'mobile first conversion landing', "
                            "'react performance image optimization'"
                        )
                    },
                    "domain": {
                        "type": "string",
                        "enum": ["style", "color", "typography", "ux", "stack", "product", "landing"],
                        "description": (
                            "Domaine cible optionnel. "
                            "Omets ce paramètre pour une recherche tous domaines."
                        )
                    },
                    "k": {
                        "type": "integer",
                        "description": "Nombre de résultats (1-8, défaut 5)",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_direction",
            "description": (
                "Génère la direction design finale en JSON structuré. "
                "Appelle cette fonction UNIQUEMENT quand tu as collecté "
                "suffisamment d'informations via search_uiux."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "design_direction": {
                        "type": "object",
                        "properties": {
                            "pattern":   {"type": "string"},
                            "style":     {"type": "string"},
                            "mood":      {"type": "string"},
                            "rationale": {"type": "string"}
                        },
                        "required": ["pattern", "style", "mood", "rationale"]
                    },
                    "colors": {
                        "type": "object",
                        "properties": {
                            "primary":    {"type": "string"},
                            "secondary":  {"type": "string"},
                            "cta":        {"type": "string"},
                            "background": {"type": "string"},
                            "text":       {"type": "string"}
                        },
                        "required": ["primary", "secondary", "cta", "background", "text"]
                    },
                    "typography": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "body":    {"type": "string"},
                            "scale":   {"type": "string"}
                        },
                        "required": ["heading", "body", "scale"]
                    },
                    "key_effects":    {"type": "array", "items": {"type": "string"}},
                    "anti_patterns":  {"type": "array", "items": {"type": "string"}},
                    "ux_priorities":  {"type": "array", "items": {"type": "string"}},
                    "stack_notes":    {"type": "string"},
                    "confidence":     {"type": "string", "enum": ["high", "medium", "low"]},
                    "clarification_needed": {"type": "string", "nullable": True},
                    "searches_done":  {"type": "integer"}
                },
                "required": [
                    "design_direction", "colors", "typography",
                    "key_effects", "anti_patterns", "ux_priorities",
                    "confidence"
                ]
            }
        }
    }
]


# ── Exécution des outils ──────────────────────────────────────────────────────

def _execute_search(args: dict) -> str:
    """Exécute search_uiux et retourne les résultats formatés."""
    query = args.get("query", "")
    domain = args.get("domain", None)
    k = min(int(args.get("k", 5)), 8)

    store = get_store()
    if not store.is_built():
        return "Index RAG non disponible."

    results = store.search(query, k=k, domain_filter=domain)

    if not results:
        return f"Aucun résultat pour '{query}'."

    lines = [f"Résultats pour '{query}' ({len(results)} chunks):"]
    for r in results:
        meta = r["metadata"]
        domain_found = meta.get("domain", "?")
        score = r["score"]
        text = r["text"][:200]
        lines.append(f"\n[{domain_found}] score={score:.2f}")
        lines.append(f"  {text}")

        # Ajoute les métadonnées utiles selon le domaine
        if domain_found == "color":
            lines.append(
                f"  → primary={meta.get('primary','')} "
                f"secondary={meta.get('secondary','')} "
                f"cta={meta.get('cta','')} "
                f"bg={meta.get('background','')} "
                f"text={meta.get('text_color','')}"
            )
        elif domain_found == "typography":
            lines.append(
                f"  → heading={meta.get('heading','')} "
                f"body={meta.get('body','')} "
                f"url={meta.get('google_url','')}"
            )
        elif domain_found == "ux":
            lines.append(f"  → DO: {meta.get('do','')[:100]}")
            lines.append(f"  → AVOID: {meta.get('dont','')[:100]}")
        elif domain_found == "stack":
            lines.append(
                f"  → [{meta.get('stack','')}] "
                f"DO: {meta.get('do','')[:100]}"
            )

    return "\n".join(lines)


def _execute_tool(tool_name: str, tool_args: dict) -> str:
    """Dispatch vers le bon outil."""
    if tool_name == "search_uiux":
        return _execute_search(tool_args)
    elif tool_name == "generate_direction":
        # On retourne les args directement — c'est la direction finale
        return "__DIRECTION__"
    return f"Outil inconnu: {tool_name}"


# ── Boucle agentique ──────────────────────────────────────────────────────────

def _call_ollama_tools(messages: list, model: str) -> dict:
    """Appel Ollama avec support function calling + streaming.
    Gère la fragmentation des tool_calls (Deepseek, Qwen3, Gemini).
    """
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "tools": TOOLS,
        "stream": True,
        "options": {"temperature": 0.3, "top_p": 0.9},
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            content_acc = ""
            # tool_calls indexés par position pour merger les fragments
            tool_calls_map = {}  # index -> {id, name, arguments_str}
            in_think = False

            for line in resp:
                line = line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = chunk.get("message", {})

                # Accumule le texte — masque le thinking mode
                token = msg.get("content", "")
                if token:
                    content_acc += token
                    if "<think>" in token:
                        in_think = True
                    if "</think>" in token:
                        in_think = False
                        continue
                    if not in_think:
                        print(token, end="", flush=True)

                # Accumule et merge les tool_calls fragmentés
                for tc in msg.get("tool_calls", []):
                    idx = tc.get("index", len(tool_calls_map))
                    fn = tc.get("function", {})

                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": tc.get("id", f"call_{idx}"),
                            "name": fn.get("name", ""),
                            "arguments_str": ""
                        }

                    # Merge le nom si fragmenté
                    if fn.get("name"):
                        tool_calls_map[idx]["name"] = fn["name"]

                    # Merge les arguments (peuvent arriver en plusieurs chunks)
                    args = fn.get("arguments", "")
                    if isinstance(args, str):
                        tool_calls_map[idx]["arguments_str"] += args
                    elif isinstance(args, dict):
                        # Déjà parsé — stocker direct
                        tool_calls_map[idx]["arguments_str"] = json.dumps(args)

                if chunk.get("done"):
                    if content_acc and not in_think:
                        print()
                    break

            # Reconstruit les tool_calls finaux avec arguments parsés
            tool_calls_final = []
            for idx in sorted(tool_calls_map.keys()):
                tc = tool_calls_map[idx]
                args_str = tc["arguments_str"].strip()
                try:
                    args = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls_final.append({
                    "function": {"name": tc["name"], "arguments": args}
                })

            return {"message": {
                "role": "assistant",
                "content": content_acc,
                "tool_calls": tool_calls_final
            }}

    except urllib.error.URLError as e:
        raise ConnectionError(f"Ollama indisponible: {e}")


def _try_parse_direction(text: str, searches_done: int):
    """Extrait une direction JSON depuis une réponse texte brute."""
    import re

    if "<think>" in text:
        end = text.rfind("</think>")
        if end != -1:
            text = text[end + len("</think>"):].strip()

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if "design_direction" in data:
                data["searches_done"] = searches_done
                return data
        except json.JSONDecodeError:
            pass

    brace_start = text.find("{")
    if brace_start != -1:
        depth = 0
        for i, ch in enumerate(text[brace_start:], brace_start):
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(text[brace_start:i + 1])
                        if "design_direction" in data:
                            data["searches_done"] = searches_done
                            return data
                    except json.JSONDecodeError:
                        break
    return None


def run_agent(analysis: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Boucle agentique principale.
    Qwen appelle search_uiux autant de fois que nécessaire,
    puis appelle generate_direction quand il est prêt.
    """
    system_prompt = f"""Tu es un expert UI/UX senior. Tu dois générer une direction design complète.

PROJET:
- Requête: {analysis['original_query']}
- Type: {analysis['product_type']}
- Stack: {analysis['stack']}
- Styles détectés: {', '.join(analysis['styles'])}

PROCESSUS:
1. Utilise search_uiux pour rechercher des informations pertinentes
2. Fais plusieurs recherches avec des angles différents (style, couleurs, UX, stack...)
3. Quand tu as suffisamment d'info, appelle generate_direction avec la direction complète

Commence par rechercher des informations.
Sois efficace : 3-4 recherches ciblées suffisent."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Génère la direction design pour: {analysis['original_query']}"}
    ]

    searches_done = 0
    final_direction = None

    print(f"\n🤖 Agent RAG démarré...\n")

    for iteration in range(MAX_ITERATIONS):
        response = _call_ollama_tools(messages, model)
        message = response.get("message", {})

        # Ajoute la réponse à l'historique
        messages.append(message)

        tool_calls = message.get("tool_calls", [])

        # Pas d'appel d'outil → le modèle a répondu en texte
        # Certains modèles (Gemini, Deepseek) écrivent le JSON directement
        if not tool_calls:
            text = message.get("content", "")
            if text:
                # Tente de parser une direction JSON dans la réponse texte
                parsed = _try_parse_direction(text, searches_done)
                if parsed:
                    print(f"\n  ✅ Direction extraite du texte ({searches_done} recherche(s))")
                    return parsed
                print(f"  Réponse texte sans direction: {text[:80]}")
            break

        # Traite chaque appel d'outil
        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            tool_name = fn.get("name", "")
            tool_args = fn.get("arguments", {})

            # Parse les arguments si c'est une string
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}

            if tool_name == "search_uiux":
                query = tool_args.get("query", "")
                domain = tool_args.get("domain", "tous")
                k = tool_args.get("k", 5)
                searches_done += 1
                print(f"  🔍 Recherche #{searches_done}: '{query}' [{domain}] k={k}")

                result = _execute_search(tool_args)

                messages.append({
                    "role": "tool",
                    "content": result
                })

            elif tool_name == "generate_direction":
                print(f"\n  ✅ Direction générée après {searches_done} recherche(s)")
                final_direction = tool_args
                final_direction["searches_done"] = searches_done
                return final_direction

    # Fallback si la boucle se termine sans generate_direction
    if final_direction is None:
        return {
            "error": "L'agent n'a pas généré de direction",
            "searches_done": searches_done
        }

    return final_direction


# ── Interface compatible avec get_design_direction ────────────────────────────

def get_design_direction_agent(analysis: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Remplace get_design_direction() de ollama_client.py.
    Utilise la boucle agentique au lieu d'une seule passe.
    """
    try:
        direction = run_agent(analysis, model)
        return direction
    except Exception as e:
        return {"error": str(e)}