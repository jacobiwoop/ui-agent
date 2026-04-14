import json
import os
from ollama_client import _call_ollama, _parse_json_response, DEFAULT_MODEL

def plan_page_content(synthesis: dict, strategies: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Pour chaque direction, sélectionne les modules et crée des briefs de contenu.
    """
    
    available_modules = [
        "hero", "benefits", "problems", "description", "how-it-works", 
        "comparison", "testimonials", "trust", "urgency", "cod-form", "cta-final"
    ]

    prompt = f"""Tu es un UX Planner & Architecte de Conversion. 
À partir de la synthèse produit et des 3 stratégies marketing, planifie le contenu détaillé pour CHAQUE direction.

SYNTHÈSE PRODUIT :
{json.dumps(synthesis, indent=2, ensure_ascii=False)}

STRATÉGIES :
{json.dumps(strategies, indent=2, ensure_ascii=False)}

MODULES DISPONIBLES :
{available_modules}

MISSION :
Pour chaque direction marketing, choisis 6 à 8 modules parmi la liste et rédige un "brief de copie" précis pour chacun (ce qu'il doit dire, l'argument clé).

FORMAT DE SORTIE (JSON UNIQUEMENT) :
{{
  "plans": [
    {{
      "direction_name": "Nom de la direction",
      "modules": [
        {{
          "id": "hero",
          "brief": "Titre accrocheur sur la performance, focus sur la semelle EVA...",
          "key_elements": ["Badge Urgence", "Titre HIIT", "Bouton CTA"]
        }},
        ... 
      ]
    }},
    ... (3 fois)
  ]
}}

RÉPONSE JSON :
"""

    messages = [
        {"role": "system", "content": "Tu es un architecte de conversion e-commerce expert."},
        {"role": "user", "content": prompt}
    ]

    print(f"🗺️  Planification des contenus par direction...")
    raw_response = _call_ollama(messages, model, stream=False)
    plans = _parse_json_response(raw_response)
    
    return plans

if __name__ == "__main__":
    synth_path = "product_synthesis.json"
    strat_path = "marketing_strategies.json"
    
    if os.path.exists(synth_path) and os.path.exists(strat_path):
        with open(synth_path, "r", encoding="utf-8") as fs, open(strat_path, "r", encoding="utf-8") as fg:
            synth = json.load(fs)
            strat = json.load(fg)
            
            plans = plan_page_content(synth, strat)
            
            output_file = "content_plans.json"
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(plans, out, indent=2, ensure_ascii=False)
            
            print(f"✅ Plans de contenu générés dans {output_file}")
    else:
        print(f"❌ Erreur : Fichiers manquants. Lance d'abord copywriter.py et strategy_agent.py.")
