import json
import os
from ollama_client import _call_ollama, _parse_json_response, DEFAULT_MODEL

def generate_marketing_strategies(synthesis: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Génère 3 directions rédactionnelles basées sur la synthèse produit.
    """
    
    prompt = f"""Tu es un Stratège Marketing Digital expert. 
À partir de la synthèse produit ci-dessous, définis 3 stratégies (directions rédactionnelles) distinctes pour une page de vente.

SYNTHÈSE PRODUIT :
{json.dumps(synthesis, indent=2, ensure_ascii=False)}

DIRECTIONS À GÉNÉRER :
1. "Urgence & Performance" : Ton direct, dynamique, focus sur l'efficacité, la rapidité, la rareté.
2. "Histoire & Style de Vie" : Ton narratif, inspirant, focus sur le quotidien de l'utilisateur, l'émotion.
3. "Confiance & Expertise" : Ton rassurant, analytique, focus sur les preuves techniques, les bénéfices concrets.

RÉCOMPENSE : 
Retourne un JSON avec la structure :
{{
  "directions": [
    {{
      "name": "Nom de la direction",
      "angle": "Description de l'angle d'attaque",
      "tone": "Ton à adopter",
      "focus_points": ["Point 1", "Point 2", "Point 3"]
    }},
    ... (3 fois)
  ]
}}

RÉPONSE JSON :
"""

    messages = [
        {"role": "system", "content": "Tu es un stratège marketing expert qui parle français."},
        {"role": "user", "content": prompt}
    ]

    print(f"🎯 Définition des stratégies marketing...")
    raw_response = _call_ollama(messages, model, stream=False)
    strategies = _parse_json_response(raw_response)
    
    return strategies

if __name__ == "__main__":
    # Test avec la synthèse générée
    synth_path = "product_synthesis.json"
    if os.path.exists(synth_path):
        with open(synth_path, "r", encoding="utf-8") as f:
            synth = json.load(f)
            
            strategies = generate_marketing_strategies(synth)
            
            output_file = "marketing_strategies.json"
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(strategies, out, indent=2, ensure_ascii=False)
            
            print(f"✅ Stratégies définies et sauvegardées dans {output_file}")
    else:
        print(f"❌ Erreur : {synth_path} introuvable. Lance d'abord copywriter.py.")
