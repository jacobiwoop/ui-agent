import subprocess
import os
import json
import tempfile

def generate_html(spec_path: str, product_query: str, model: str, content_data: dict = None, cwd: str = None) -> str:
    """Appelle OpenCode pour générer le code HTML final."""
    
    # 1. Lire la spécification du design system (chemin relatif au CWD ou absolu)
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_content = f.read()
    except Exception as e:
        return f"Erreur lors de la lecture de la spec : {str(e)}"

    # ... (prompt preparation) ...
    full_prompt = f"""RÈGLES DE DESIGN (MASTER SPECIFICATION) :
{spec_content}

REQUÊTE PRODUIT :
{product_query}
{content_instruction}

MISSION :
Génère une page HTML unique, complète et professionnelle pour ce produit.
- Utilise Tailwind CSS (via CDN) pour le style.
- Intègre les polices Google Fonts mentionnées dans la spec.
- Respecte scrupuleusement les couleurs, les arrondis (radius) et les animations de la spec.
- SÉCURITÉ : Ne jamais appliquer `pointer-events: none` sur la balise `body` ou tout conteneur englobant. Tous les éléments interactifs (boutons, inputs) DOIVENT être cliquables.
- Implémente tous les modules listés dans le contenu rédactionnel (Hero, Benefits, etc.).
- Le code doit être dans un seul bloc de code HTML.
"""

    print(f"\n🚀 Génération du HTML via OpenCode (Modèle: {model})...")
    
    # Préparation de l'environnement (PATH dynamique)
    env = os.environ.copy()
    home = os.path.expanduser("~")
    env["PATH"] = f"{home}/.opencode/bin:{home}/.bun/bin:{env.get('PATH', '')}"

    # 4. Ajuster le nom du modèle pour OpenCode (format provider/model demandé)
    if "/" not in model:
        if "qwen3.5" in model:
            opencode_model = "ollama-cloud/qwen3-coder-next"
        else:
            opencode_model = f"ollama-cloud/{model}"
    else:
        opencode_model = model

    # Utiliser le CWD fourni ou par défaut la racine du projet
    working_dir = cwd if cwd else os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    try:
        cmd = [
            "opencode", "run", 
            "--model", opencode_model, 
            "--dangerously-skip-permissions", 
            full_prompt
        ]
        
        result = subprocess.run(
            cmd, 
            env=env, 
            capture_output=True, 
            text=True, 
            timeout=1200, # 20 minutes
            cwd=working_dir
        )
        
        if result.returncode != 0:
            return f"Erreur OpenCode (code {result.returncode}) : {result.stderr or result.stdout}"
        
        raw_output = result.stdout.strip()
        
        # 5. Extraction du code HTML
        if "<html>" in raw_output.lower() or "<!doctype html>" in raw_output.lower():
            import re
            start_match = re.search(r"(<!DOCTYPE html>|<html>)", raw_output, re.IGNORECASE)
            end_match = raw_output.lower().rfind("</html>")
            
            if start_match and end_match != -1:
                return raw_output[start_match.start():end_match + 7]

        # 6. Fallback : Si opencode a créé un fichier
        if ".html" in raw_output:
            import re
            # Chercher un chemin absolu ou relatif dans le dossier de travail
            file_match = re.search(r"([\w\-/.]+\.html)", raw_output)
            if file_match:
                filename = file_match.group(1)
                full_path = os.path.join(working_dir, filename) if not os.path.isabs(filename) else filename
                if os.path.exists(full_path):
                    print(f"   📂 Fichier détecté : {full_path}. Lecture en cours...")
                    with open(full_path, "r", encoding="utf-8") as f:
                        return f.read()

        return raw_output
    except subprocess.TimeoutExpired:
        return "Erreur : Timeout de 20 minutes dépassé pour la génération du code."
    except Exception as e:
        return f"Erreur lors de l'appel de OpenCode : {str(e)}"

if __name__ == "__main__":
    # Petit test standalone si lancé directement
    import sys
    if len(sys.argv) > 1:
        # Usage: python3 coder.py <spec_path> <query> [model]
        path = sys.argv[1]
        query = sys.argv[2]
        mdl = sys.argv[3] if len(sys.argv) > 3 else "qwen3.5:cloud"
        print(generate_html(path, query, mdl))
    else:
        print("Usage test: python3 coder.py <spec_path> <query> [model]")
