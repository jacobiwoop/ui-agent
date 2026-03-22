"""
Prompt Builder — fusionne les données CSV du skill avec le contexte utilisateur
pour construire un prompt enrichi pour Ollama/Qwen.
"""

import json


SYSTEM_PROMPT = """Tu es un expert UI/UX senior. Tu analyses des projets et fournis 
une DIRECTION DE DESIGN claire et structurée — pas du code, juste la stratégie.

Ta réponse doit toujours suivre ce format JSON strict :
{
  "design_direction": {
    "pattern": "...",
    "style": "...",
    "mood": "...",
    "rationale": "..."
  },
  "colors": {
    "primary": "#...",
    "secondary": "#...",
    "cta": "#...",
    "background": "#...",
    "text": "#..."
  },
  "typography": {
    "heading": "...",
    "body": "...",
    "scale": "..."
  },
  "key_effects": ["...", "..."],
  "anti_patterns": ["...", "..."],
  "ux_priorities": ["...", "..."],
  "stack_notes": "...",
  "confidence": "high|medium|low",
  "clarification_needed": null
}

Si la requête est trop vague, mets "clarification_needed" avec une question précise.
Réponds UNIQUEMENT en JSON valide, aucun texte autour."""


def _format_skill_data(context: dict) -> str:
    """Formate les données du skill en texte lisible pour le prompt."""
    lines = []

    if context.get("styles"):
        lines.append("## STYLES RECOMMANDÉS (base de données UI/UX):")
        for r in context["styles"][:2]:
            name = r.get("Style Category", "")
            keywords = r.get("Keywords", "")[:100]
            best_for = r.get("Best For", "")[:100]
            effects = r.get("Effects & Animation", "")[:80]
            lines.append(f"- {name}: {keywords}")
            lines.append(f"  Best for: {best_for}")
            if effects:
                lines.append(f"  Effects: {effects}")

    if context.get("colors"):
        lines.append("\n## PALETTES DE COULEURS:")
        for r in context["colors"][:2]:
            ptype = r.get("Product Type", "")
            primary = r.get("Primary (Hex)", "")
            secondary = r.get("Secondary (Hex)", "")
            cta = r.get("CTA (Hex)", "")
            bg = r.get("Background (Hex)", "")
            lines.append(f"- {ptype}: primary={primary}, secondary={secondary}, cta={cta}, bg={bg}")

    if context.get("typography"):
        lines.append("\n## TYPOGRAPHIE:")
        for r in context["typography"][:2]:
            name = r.get("Font Pairing Name", "")
            heading = r.get("Heading Font", "")
            body = r.get("Body Font", "")
            mood = r.get("Mood/Style Keywords", "")[:80]
            lines.append(f"- {name}: heading={heading}, body={body} ({mood})")

    if context.get("ux_guidelines"):
        lines.append("\n## GUIDELINES UX CRITIQUES:")
        for r in context["ux_guidelines"][:3]:
            issue = r.get("Issue", "")
            do_ = r.get("Do", "")[:100]
            dont = r.get("Don't", "")[:80]
            severity = r.get("Severity", "")
            if issue:
                lines.append(f"- [{severity}] {issue}: DO={do_}")
                if dont:
                    lines.append(f"  DON'T: {dont}")

    if context.get("stack_guidelines"):
        lines.append("\n## GUIDELINES STACK:")
        for r in context["stack_guidelines"][:2]:
            guideline = r.get("Guideline", "")
            desc = r.get("Description", "")[:100]
            if guideline:
                lines.append(f"- {guideline}: {desc}")

    return "\n".join(lines)


def build_prompt(analysis: dict, skill_context: dict, history: list = None) -> list:
    """
    Construit les messages pour Ollama.
    
    Returns:
        list: messages au format [{"role": "...", "content": "..."}]
    """
    skill_data = _format_skill_data(skill_context)

    user_content = f"""REQUÊTE: {analysis['original_query']}

CONTEXTE DÉTECTÉ:
- Type de produit: {analysis['product_type']}
- Stack: {analysis['stack']}
- Styles détectés: {', '.join(analysis['styles'])}

DONNÉES DE RÉFÉRENCE UI/UX:
{skill_data}

Génère la direction design JSON pour ce projet."""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Injecte l'historique si présent (pour le feedback)
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_content})
    return messages


def build_feedback_prompt(previous_direction: dict, feedback: str) -> dict:
    """Construit le message de feedback pour raffiner la direction."""
    return {
        "role": "user",
        "content": f"""FEEDBACK SUR LA DIRECTION PRÉCÉDENTE:
{feedback}

Direction précédente:
{json.dumps(previous_direction, indent=2, ensure_ascii=False)}

Génère une direction révisée en tenant compte du feedback. Réponds en JSON valide uniquement."""
    }
