import json
import os
from ollama_client import _call_ollama, _parse_json_response, DEFAULT_MODEL

def generate_module_content(plan: dict, synthesis: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Génère le contenu textuel final pour tous les modules d'une direction donnée.
    """
    direction_name = plan['direction_name']
    modules_to_generate = plan['modules']

    prompt = f"""Tu es un Copywriter de Conversion senior. 
Ta mission est de rédiger le contenu textuel final pour une page de vente en suivant une stratégie précise.

STRATÉGIE : {direction_name}
SYNTHÈSE DU PRODUIT :
{json.dumps(synthesis, indent=2, ensure_ascii=False)}

PLANS DES MODULES :
{json.dumps(modules_to_generate, indent=2, ensure_ascii=False)}

CONSIGNES :
1. Pour CHAQUE module listé, rédige le texte final (Titres, Sous-titres, corps de texte, libellés de boutons).
2. Respecte scrupuleusement le TON et l'ANGLE de la stratégie.
3. Sois percutant, utilise des techniques de copywriting (AIDA, PAS).
4. Langue : Français.

FORMAT DE SORTIE (JSON UNIQUEMENT) :
{{
  "direction": "{direction_name}",
  "content": {{
    "module_id": {{
       "title": "Texte du titre",
       "subtitle": "Texte du sous-titre",
       "body": "Corps du texte ou liste de points",
       "cta": "Texte du bouton"
    }},
    ...
  }}
}}

RÉPONSE JSON :
"""

    messages = [
        {"role": "system", "content": "Tu es un copywriter de conversion expert qui parle français."},
        {"role": "user", "content": prompt}
    ]

    print(f"✍️  Génération du contenu pour la direction : {direction_name}...")
    raw_response = _call_ollama(messages, model, stream=False)
    content = _parse_json_response(raw_response)
    
    return content

if __name__ == "__main__":
    synth_path = "product_synthesis.json"
    plans_path = "content_plans.json"
    
    if os.path.exists(synth_path) and os.path.exists(plans_path):
        with open(synth_path, "r", encoding="utf-8") as fs, open(plans_path, "r", encoding="utf-8") as fp:
            synthesis = json.load(fs)
            plans_data = json.load(fp)
            
            final_results = []
            
            # Pour chaque direction planifiée
            for plan in plans_data.get('plans', []):
                result = generate_module_content(plan, synthesis)
                final_results.append(result)
            
            output_file = "final_content.json"
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump({"directions_content": final_results}, out, indent=2, ensure_ascii=False)
            
            print(f"✅ Contenu final généré dans {output_file}")
    else:
        print(f"❌ Erreur : Fichiers manquants. Lance d'abord la chaîne précédente.")
