import sys
import os
from coder import generate_html

def test():
    # On choisit une spec existante dans exports/
    spec_path = "exports/system_ecommerce_professional_20260414_192826.md"
    query = "Chaussures de sport haute performance pour marathon"
    model = "qwen3.5:cloud"  # Sera transformé en ollama-cloud/qwen3.5:397b par coder.py

    if not os.path.exists(spec_path):
        print(f"❌ Erreur : Fichier {spec_path} introuvable.")
        return

    print(f"🧪 Test de génération HTML avec OpenCode...")
    print(f"   Spec: {spec_path}")
    print(f"   Query: {query}")
    print("-" * 40)

    html = generate_html(spec_path, query, model)

    if html.startswith("Erreur"):
        print(f"❌ Échec du test :\n{html}")
    elif len(html) < 100:
        print(f"⚠️ Résultat suspect (trop court) :\n{html}")
    else:
        print(f"✅ Succès ! Code HTML généré ({len(html)} caractères).")
        
        # Aperçu du début et de la fin
        print("\n--- Aperçu (début) ---")
        print(html[:300] + "...")
        print("\n--- Aperçu (fin) ---")
        print("..." + html[-300:])

        # Sauvegarde du test
        test_output = "exports/test_result.html"
        with open(test_output, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n💾 Résultat sauvegardé dans {test_output}")

if __name__ == "__main__":
    test()
