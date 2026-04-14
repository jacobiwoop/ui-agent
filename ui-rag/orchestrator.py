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

def run_full_pipeline(url: str, model: str = "qwen3.5:cloud"):
    print(f"\n🚀 DÉMARRAGE DE L'ORCHESTRATION POUR : {url}")
    
    # 1. SCRAPE
    print("\n--- 1. SCRAPING ALIBABA ---")
    run_alibaba_extraction(url)
    with open("alibaba_result.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f).get('data', {})
    
    if not raw_data.get('success'):
        print("❌ Échec du scraping. Arrêt.")
        return

    # 2. SYNTHÈSE
    print("\n--- 2. SYNTHÈSE PRODUIT ---")
    synthesis = synthesize_product_data(raw_data, model=model)
    with open("product_synthesis.json", "w", encoding="utf-8") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)

    # 3. GÉNÉRATION AUTOMATIQUE DU DESIGN (Style)
    print("\n--- 3. GÉNÉRATION DU DESIGN SYSTEM (STYLE) ---")
    product_query = synthesis.get('title', 'produit e-commerce')
    print(f"   🎨 Analyse du style pour : {product_query}")
    direction, analysis = run_pipeline(product_query, model, as_json=True, verbose=False)
    
    print("   🏗️  Expansion vers Master Specification...")
    system_prompt = expand_to_system_prompt(direction, analysis, model=model)
    
    # Sauvegarde de la spec pour OpenCode
    spec_path = "exports/current_style_spec.md"
    os.makedirs("exports", exist_ok=True)
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(system_prompt)
    print(f"   ✅ Spec générée : {spec_path}")

    # 4. STRATÉGIES
    print("\n--- 4. DÉFINITION DES STRATÉGIES ---")
    strategies = generate_marketing_strategies(synthesis, model=model)
    with open("marketing_strategies.json", "w", encoding="utf-8") as f:
        json.dump(strategies, f, indent=2, ensure_ascii=False)

    # 5. PLANIFICATION
    print("\n--- 5. PLANIFICATION DES MODULES ---")
    plans_data = plan_page_content(synthesis, strategies, model=model)
    with open("content_plans.json", "w", encoding="utf-8") as f:
        json.dump(plans_data, f, indent=2, ensure_ascii=False)

    # 6. RÉDACTION DES MODULES
    print("\n--- 6. RÉDACTION DES MODULES (DIRECTION 1) ---")
    first_plan = plans_data.get('plans', [])[0]
    final_content = generate_module_content(first_plan, synthesis, model=model)

    # 7. GÉNÉRATION HTML FINAL
    print("\n--- 7. GÉNÉRATION HTML FINAL (FUSION STYLE + CONTENU) ---")
    html_code = generate_html(spec_path, product_query, model, content_data=final_content)
    
    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"exports/final_page_{timestamp}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_code)
    
    print(f"\n✨ PAGE TERMINÉE ! Disponible ici : {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrateur UI-RAG")
    parser.add_argument("url", help="URL Alibaba du produit")
    parser.add_argument("--model", default="qwen3.5:cloud", help="Modèle à utiliser")
    args = parser.parse_args()

    run_full_pipeline(args.url, args.model)
