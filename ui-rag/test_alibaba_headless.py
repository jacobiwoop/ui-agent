import requests
import json
import os

def run_alibaba_extraction(target_url, output_file="alibaba_result.json"):
    """
    Envoie un script JavaScript au serveur headless pour extraire les données d'Alibaba.
    """
    
    # Configuration
    ENDPOINT = "https://headless-wof9.onrender.com/run-file"
    
    # ... (template code) ...
    js_script = js_template.replace("TARGET_URL_PLACEHOLDER", target_url)

    print(f"📡 Envoi du script au serveur pour l'URL : {target_url}")
    
    # Préparation du multipart/form-data
    files = {
        'file': ('code.js', js_script, 'application/javascript'),
        'timeout': (None, '90000')
    }
    
    try:
        response = requests.post(ENDPOINT, files=files)
        response.raise_for_status()
        
        result = response.json()
        
        # Sauvegarde du résultat
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        # Affichage rapide (on accède à 'data' car le serveur enveloppe la réponse)
        data = result.get('data', {})
        
        if data.get('success'):
            print(f"✅ Extraction réussie !")
            print(f"🏆 Titre : {data.get('title')}")
            print(f"📸 Images : {len(data.get('images', []))} images trouvées")
            print(f"📊 Attributs : {len(data.get('attributes', {}))} caractéristiques extraites")
        else:
            # Si le serveur renvoie une erreur au niveau racine ou dans data
            error_msg = result.get('error') or data.get('error')
            print(f"❌ Erreur : {error_msg}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la requête : {str(e)}")

if __name__ == "__main__":
    TEST_URL = "https://french.alibaba.com/product-detail/China-Factory-Woven-Weave-Hand-Knit-1600654196070.html?spm=a2700.7724857.0.0.613a5ec2x4aC1I"
    run_alibaba_extraction(TEST_URL)
