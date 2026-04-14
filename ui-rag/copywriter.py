import json
import os
from ollama_client import _call_ollama, _parse_json_response, DEFAULT_MODEL

def synthesize_product_data(raw_data: dict, model: str = DEFAULT_MODEL) -> dict:
    """
    Transforme les données brutes d'Alibaba en une synthèse propre pour le copywriting.
    """
    
    prompt = f"""Tu es un Copywriter Expert E-commerce. 
Ta mission est de transformer les données brutes d'Alibaba ci-dessous en une synthèse marketing propre, captivante et structurée.

DONNÉES BRUTES :
{json.dumps(raw_data, indent=2, ensure_ascii=False)}

RÈGLES :
1. Titre : Crée un titre court, élégant et mémorable (max 10 mots). Enlève les termes "China Factory", "Supplier", etc.
2. Synthèse : Rédige 2-3 paragraphes qui vendent le bénéfice principal et l'émotion du produit.
3. Caractéristiques : Liste les 5 points techniques les plus importants.
4. Langue : Réponds en Français.
5. Format : Retourne UNIQUEMENT un JSON avec les clés : "title", "synthesis", "features" (liste), "images" (garder les 5 meilleures URLs).

RÉPONSE JSON :
"""

    messages = [
        {"role": "system", "content": "Tu es un copywriter e-commerce expert qui parle français."},
        {"role": "user", "content": prompt}
    ]

    print(f"✍️  Synthèse du produit en cours...")
    raw_response = _call_ollama(messages, model, stream=False)
    synthesized = _parse_json_response(raw_response)
    
    return synthesized

if __name__ == "__main__":
    # Test avec le dernier résultat alibaba
    result_path = "alibaba_result.json"
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # On prend la partie 'data' si elle existe
            data = raw.get('data', raw)
            
            synth = synthesize_product_data(data)
            
            output_file = "product_synthesis.json"
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(synth, out, indent=2, ensure_ascii=False)
            
            print(f"✅ Synthèse terminée et sauvegardée dans {output_file}")
    else:
        print(f"❌ Erreur : {result_path} introuvable. Lance d'abord le scraper.")
