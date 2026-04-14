import json
import urllib.request
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = """Tu es un **Directeur de Création et Architecte Design System Senior**. 
Ta spécialité est de transformer des directions design simples en documents de spécifications techniques ultra-détaillés (Master Specifications) qui serviront de base à une génération de code.

STRUCTURE DU DOCUMENT À GÉNÉRER (MARKDOWN) :

1. <role> : Définis le rôle de l'IA (Expert UI/UX, Designer Minimaliste, etc.)
2. <design-system> : 
    - **Philosophy** : Le concept profond du design.
    - **Visual Vibe/DNA** : L'ambiance visuelle en détails.
    - **Design Token System** : Couleurs (Hex + Nom), Typographie (Font + Scale), Radius (px), Shadows (Bézier), Textures (CSS).
    - **Component Stylings** : Règles précises pour Buttons, Cards, Forms, Layout.
    - **Effects & Animation** : Transitions, Hovers, Timings.
    - **Accessibility & Bold Choices** : Les choix radicaux qui rendent le design unique.

RÈGLES :
- Sois technique et précis (utilise des valeurs CSS exactes).
- Incorpore les "Notes Stack" fournies par le RAG.
- SÉCURITÉ : Ne jamais appliquer `pointer-events: none` sur la balise `body` ou des conteneurs globaux. Utilise-le uniquement sur des overlays spécifiques.
- Le document doit être prêt à être utilisé comme System Prompt pour une autre IA.
- Ne fais pas de blabla au début ou à la fin. Uniquement le Markdown.
"""

def expand_to_system_prompt(direction: dict, analysis: dict, model: str) -> str:
    """Appelle Ollama pour transformer la direction RAG en un prompt complet."""
    
    user_context = f"""Voici la direction design générée par le RAG :
    
    PRODUIT : {analysis['product_type']}
    STYLES : {', '.join(analysis['styles'])}
    DIRECTION : {json.dumps(direction.get('design_direction', {}), indent=2)}
    COULEURS : {json.dumps(direction.get('colors', {}), indent=2)}
    TYPOGRAPHIE : {json.dumps(direction.get('typography', {}), indent=2)}
    EFFETS : {', '.join(direction.get('key_effects', []))}
    STAKE NOTES : {direction.get('stack_notes', '')}
    
    Rédige maintenant le Master Design Specification complet en Markdown, en suivant la structure demandée.
    """

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_context}
        ],
        "stream": False,
        "options": {"temperature": 0.7}
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"]
    except Exception as e:
        return f"Erreur lors de l'expansion : {str(e)}"
