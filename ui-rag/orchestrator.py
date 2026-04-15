import json
import os
import argparse
from datetime import datetime

# Import des agents
from test_alibaba_headless import run_alibaba_extraction
from copywriter import synthesize_product_data
from strategy_agent import generate_marketing_strategies
from planner import plan_page_content
from module_agent import generate_module_content
from coder import generate_html

# Import des fonctions de main.py pour l'automatisation du design
from main import run_pipeline, expand_to_system_prompt

def run_full_pipeline(url: str, model: str = "qwen3.5:cloud", session_id: str = None):
    # Setup session directory
    if session_id:
        base_dir = os.path.join("sessions", session_id)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.join("exports", f"run_{timestamp}")
    
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "exports"), exist_ok=True) # For consistency with coder expectations
    
    print(f"\n🚀 DÉMARRAGE DE L'ORCHESTRATION POUR : {url}")
    print(f"📂 DOSSIER DE SESSION : {base_dir}")
    
    # Paths for session files
    alibaba_path = os.path.join(base_dir, "alibaba_result.json")
    synthesis_path = os.path.join(base_dir, "product_synthesis.json")
    spec_path = os.path.join(base_dir, "style_spec.md")
    strategies_path = os.path.join(base_dir, "marketing_strategies.json")
    plans_path = os.path.join(base_dir, "content_plans.json")

    # 1. SCRAPE
    print("\n--- 1. SCRAPING ALIBABA ---")
    run_alibaba_extraction(url, output_file=alibaba_path)
    
    if not os.path.exists(alibaba_path):
        print("❌ Fichier alibaba_result non trouvé. Arrêt.")
        return

    with open(alibaba_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f).get('data', {})
    
    if not raw_data.get('success'):
        print(f"❌ Échec du scraping : {raw_data.get('error')}. Arrêt.")
        return

    # 2. SYNTHÈSE
    print("\n--- 2. SYNTHÈSE PRODUIT ---")
    synthesis = synthesize_product_data(raw_data, model=model)
    with open(synthesis_path, "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)

    # 3. GÉNÉRATION AUTOMATIQUE DU DESIGN (Style)
    print("\n--- 3. GÉNÉRATION DU DESIGN SYSTEM (STYLE) ---")
    product_query = synthesis.get('title', 'produit e-commerce')
    print(f"   🎨 Analyse du style pour : {product_query}")
    direction, analysis = run_pipeline(product_query, model, as_json=True, verbose=False)
    
    print("   🏗️  Expansion vers Master Specification...")
    system_prompt = expand_to_system_prompt(direction, analysis, model=model)
    
    # Sauvegarde de la spec pour OpenCode
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(system_prompt)
    print(f"   ✅ Spec générée : {spec_path}")

    # 4. STRATÉGIES
    print("\n--- 4. DÉFINITION DES STRATÉGIES ---")
    strategies = generate_marketing_strategies(synthesis, model=model)
    with open(strategies_path, "w", encoding="utf-8") as f:
        json.dump(strategies, f, indent=2, ensure_ascii=False)

    # 5. PLANIFICATION
    print("\n--- 5. PLANIFICATION DES MODULES ---")
    plans_data = plan_page_content(synthesis, strategies, model=model)
    with open(plans_path, "w", encoding="utf-8") as f:
        json.dump(plans_data, f, indent=2, ensure_ascii=False)

    # 6. RÉDACTION DES MODULES
    print("\n--- 6. RÉDACTION DES MODULES (DIRECTION 1) ---")
    plans = plans_data.get('plans', [])
    if not plans:
        print("❌ Aucun plan généré. Arrêt.")
        return
        
    first_plan = plans[0]
    final_content = generate_module_content(first_plan, synthesis, model=model)

    # 7. GÉNÉRATION HTML FINAL
    print("\n--- 7. GÉNÉRATION HTML FINAL (FUSION STYLE + CONTENU) ---")
    # Note: coder.generate_html will run OpenCode.
    # We should ensure OpenCode runs in base_dir to avoid file conflicts.
    html_code = generate_html(spec_path, product_query, model, content_data=final_content, cwd=base_dir)
    
    # Sauvegarde finale
    output_filename = f"final_page.html"
    output_path = os.path.join(base_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_code)
    
    # Copy to global exports for backup/easy access
    global_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    global_output = f"exports/final_page_{session_id or global_timestamp}.html"
    os.makedirs("exports", exist_ok=True)
    with open(global_output, "w", encoding="utf-8") as f:
        f.write(html_code)

    print(f"\n✨ PAGE TERMINÉE !")
    print(f"📍 Session : {output_path}")
    print(f"📍 Global  : {global_output}")
    
    return global_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrateur UI-RAG")
    parser.add_argument("url", help="URL Alibaba du produit")
    parser.add_argument("--model", default="qwen3.5:cloud", help="Modèle à utiliser")
    args = parser.parse_args()

    run_full_pipeline(args.url, args.model)
