from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import sys
import argparse

def get_amazon_price(url):
    """
    Récupère le prix d'un article Amazon avec Selenium
    """
    # Configuration du navigateur en mode headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    
    try:
        # Option 1 : Initialiser le driver (il faut l'installer manuellement au préalable via https://chromedriver.chromium.org/ et le placer dans le PATH)
        #driver = webdriver.Chrome(options=chrome_options)

        # Option 1 : ChromeDriver s'installe automatiquement :
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        print("Chargement de la page...")
        driver.get(url)
        
        # Attendre que la page se charge
        time.sleep(3)
        
        # Liste des sélecteurs possibles pour le prix
        selectors = [
            (By.CLASS_NAME, 'a-price-whole'),
            (By.CSS_SELECTOR, '.a-price .a-offscreen'),
            (By.ID, 'priceblock_ourprice'),
            (By.ID, 'priceblock_dealprice'),
            (By.CSS_SELECTOR, 'span.a-price span.a-offscreen'),
            (By.XPATH, "//span[contains(@class, 'a-price')]//span[@class='a-offscreen']"),
            (By.CSS_SELECTOR, '#corePrice_feature_div .a-price .a-offscreen'),
            (By.CSS_SELECTOR, '#apex_desktop .a-price .a-offscreen'),
        ]
        
        price = None
        
        for selector_type, selector_value in selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                price_text = element.text.strip()
                
                if price_text and price_text != '':
                    price = price_text
                    print(f"✓ Prix trouvé avec le sélecteur: {selector_value}")
                    break
                    
            except TimeoutException:
                continue
            except Exception as e:
                continue
        
        # Si aucun sélecteur ne fonctionne, afficher le HTML pour debug
        if not price:
            print("\n⚠️  Aucun prix trouvé avec les sélecteurs standard.")
            print("\nRecherche de tous les éléments contenant 'EUR' ou '€'...")
            
            # Rechercher dans tout le HTML
            page_source = driver.page_source
            import re
            prices_found = re.findall(r'(\d+[,\.]\d+\s*€|€\s*\d+[,\.]\d+|\d+[,\.]\d+\s*EUR)', page_source)
            
            if prices_found:
                print(f"\nPrix potentiels trouvés dans le HTML:")
                for p in set(prices_found[:5]):  # Afficher les 5 premiers uniques
                    print(f"  - {p}")
                price = prices_found[0]
        
        if price:
            print(f"\n💰 Prix final: {price}")
            return price
        else:
            print("\n❌ Impossible de trouver le prix sur cette page")
            return None
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Parser des arguments en ligne de commande
    parser = argparse.ArgumentParser(
        description='Récupère le prix d\'un article Amazon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemples d'utilisation:
  python %(prog)s https://www.amazon.fr/dp/B0DCBB2YTR
  python %(prog)s "https://www.amazon.fr/dp/B0DCBB2YTR?th=1"
  python %(prog)s --url https://www.amazon.com/dp/B08N5WRWNW
        '''
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='URL de la page produit Amazon'
    )
    
    parser.add_argument(
        '--url',
        dest='url_flag',
        help='URL de la page produit Amazon (alternative)'
    )
    
    args = parser.parse_args()
    
    # Récupérer l'URL depuis les arguments
    url = args.url or args.url_flag
    
    if not url:
        print("❌ Erreur: Veuillez fournir une URL Amazon")
        print("\nUtilisation:")
        print(f"  python {sys.argv[0]} <URL_AMAZON>")
        print(f"\nExemple:")
        print(f"  python {sys.argv[0]} https://www.amazon.fr/dp/B0DCBB2YTR")
        sys.exit(1)
    
    # Vérifier que c'est bien une URL Amazon
    if 'amazon' not in url.lower():
        print("⚠️  Attention: L'URL ne semble pas être une URL Amazon")
        print(f"URL fournie: {url}\n")
    
    print("=" * 60)
    print("🔍 Scraper de prix Amazon avec Selenium")
    print("=" * 60)
    print(f"\nURL: {url}\n")
    
    price = get_amazon_price(url)
    
    if not price:
        print("\n💡 Conseils:")
        print("  - Vérifiez que ChromeDriver est installé")
        print("  - L'article existe peut-être plus ou est indisponible")
        print("  - Amazon peut bloquer les accès automatisés")
        sys.exit(1)
    else:
        sys.exit(0)