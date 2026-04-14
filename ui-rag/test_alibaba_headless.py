import requests
import json
import os

def run_alibaba_extraction(target_url):
    """
    Envoie un script JavaScript au serveur headless pour extraire les données d'Alibaba.
    """
    
    # Configuration
    ENDPOINT = "https://headless-wof9.onrender.com/run-file"
    
    # On utilise un template simple au lieu d'une f-string pour éviter les problèmes d'accolades { }
    js_template = """
// Script complet pour extraire titre + caractéristiques d'Alibaba
const URL = "TARGET_URL_PLACEHOLDER";

console.log('[INFO] Démarrage du script Alibaba...');

try {
  console.log('[INFO] Navigation vers Alibaba...');

  await page.goto(URL, { 
    waitUntil: 'domcontentloaded',
    timeout: 60000 
  });

  console.log('[INFO] Page chargée');

  // Attendre que le JS s'exécute
  await new Promise(r => setTimeout(r, 5000));

  // Vérifier le titre de la page
  const pageTitle = await page.title();
  console.log('[INFO] Titre de la page:', pageTitle);

  // Si captcha détecté
  if (pageTitle.includes('Captcha') || pageTitle.includes('Verification') || pageTitle.includes('Security')) {
    console.log('[WARN] Captcha détecté');

    const screenshot = await page.screenshot({ 
      encoding: 'base64',
      fullPage: false 
    });

    return {
      success: false,
      error: 'Captcha détecté',
      pageTitle,
      screenshot: `data:image/png;base64,${screenshot.substring(0, 100)}...`
    };
  }

  // 1) RÉCUPÉRER LE TITRE DU PRODUIT
  console.log('[INFO] Recherche du titre produit...');

  let productTitle = null;
  let titleSelector = null;

  const selectors = [
    'h1[title]',
    '.product-title h1',
    'h1.product-title',
    '[data-spm] h1',
    'div[class*="title"] h1',
    'h1'
  ];

  for (const selector of selectors) {
    try {
      const element = await page.$(selector);

      if (element) {
        const data = await page.evaluate(el => {
          return {
            title: el.getAttribute('title'),
            text: el.textContent,
            class: el.className,
            id: el.id
          };
        }, element);

        if (data.title || data.text) {
          productTitle = data.title || data.text.trim();
          titleSelector = selector;
          console.log('[SUCCESS] Titre trouvé:', productTitle);
          break;
        }
      }
    } catch (e) {
      continue;
    }
  }

  // 2) EXTRAIRE LES IMAGES DU PRODUIT
  console.log('[INFO] Extraction des images...');

  const images = await page.evaluate(() => {
    const imageUrls = [];
    
    const normalizeImageUrl = (url) => {
      if (!url) return null;
      if (url.startsWith('//')) {
        url = 'https:' + url;
      }
      url = url.replace(/_\\d+x\\d+q?\\d*\\.jpg/i, '.jpg');
      url = url.replace(/_\\d+x\\d+\\.jpg/i, '.jpg');
      return url;
    };

    const thumbs = document.querySelectorAll('[data-submodule="ProductImageThumbsList"] [role="group"]');
    thumbs.forEach(thumb => {
      const bgStyle = thumb.querySelector('[style*="background-image"]');
      if (bgStyle) {
        const style = bgStyle.getAttribute('style');
        const match = style.match(/url\\(['"]?([^'"()]+)['"]?\\)/);
        if (match && match[1]) {
          const url = normalizeImageUrl(match[1]);
          if (url && !imageUrls.includes(url)) {
            imageUrls.push(url);
          }
        }
      }
    });

    const mainImages = document.querySelectorAll('[data-testid="media-image"] img');
    mainImages.forEach(img => {
      const src = img.getAttribute('src') || img.getAttribute('data-src');
      if (src) {
        const url = normalizeImageUrl(src);
        if (url && !imageUrls.includes(url)) {
          imageUrls.push(url);
        }
      }
    });

    return imageUrls;
  });

  // 3) EXTRAIRE LES CARACTÉRISTIQUES (clé/valeur)
  console.log('[INFO] Extraction des caractéristiques...');

  const attributesKV = await page.evaluate(() => {
    const result = {};
    const attributeModule = document.querySelector('div[data-module-name="module_attribute"]');
    if (!attributeModule) return null;

    const rows = attributeModule.querySelectorAll('div.id-grid.id-grid-cols-\\\\[2fr_3fr\\\\]');
    rows.forEach(row => {
      try {
        const cells = row.children;
        if (cells.length < 2) return;
        const label = cells[0].textContent.trim().replace(/:$/, '');
        const value = cells[1].textContent.trim();
        if (label && value) result[label] = value;
      } catch (_) {}
    });
    return result;
  });

  // 6) RETOURNER TOUT
  return {
    success: true,
    url: page.url(),
    title: productTitle,
    images: images,
    attributes: attributesKV
  };

} catch (error) {
  console.error('[ERROR]', error.message);
  return { success: false, error: error.message };
}
"""
    
    # Injection de l'URL dans le template
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
        output_file = "alibaba_result.json"
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
