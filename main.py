from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import sys
import argparse
import re
import logging


def parse_price(price_str):
    """
    Convertit une chaîne de prix en valeur numérique et extrait la devise
    Exemple: "59,99€" -> (59.99, "€")
    """
    if not price_str:
        return None, None
    
    # Extraire la devise
    devise = None
    if '€' in price_str:
        devise = '€'
    elif 'EUR' in price_str:
        devise = 'EUR'
    elif '$' in price_str:
        devise = '$'
    elif 'USD' in price_str:
        devise = 'USD'
    elif '£' in price_str:
        devise = '£'
    elif 'GBP' in price_str:
        devise = 'GBP'
    
    # Extraire les chiffres et la virgule/point
    price_clean = re.sub(r'[^\d,.]', '', price_str)
    # Remplacer la virgule par un point
    price_clean = price_clean.replace(',', '.')
    
    try:
        return float(price_clean), devise
    except ValueError:
        return None, devise


def parse_discount(discount_str):
    """
    Convertit une chaîne de réduction en valeur numérique
    Exemple: "-27 %" -> 27
    """
    if not discount_str:
        return None
    
    # Extraire les chiffres
    match = re.search(r'(\d+)', discount_str)
    if match:
        return int(match.group(1))
    return None


def get_amazon_price(url, logger=None):
    """
    Récupère le prix d'un article Amazon avec Selenium
    
    Args:
        url: URL de la page produit Amazon
        logger: Logger pour afficher les messages de debug
    
    Returns:
        [prix_vente, devise, prix_base, pourcentage_promo]
        - prix_vente: float, prix actuel de vente
        - devise: str, devise du prix (€, $, £, etc.)
        - prix_base: float ou None, prix original si en promotion
        - pourcentage_promo: int ou None, pourcentage de réduction
    """
    # Configuration du navigateur en mode headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    debug = logger and logger.level <= logging.DEBUG
    
    try:
        # Initialiser le driver
        driver = webdriver.Chrome(options=chrome_options)
        
        if logger:
            logger.info("Chargement de la page...")
        
        driver.get(url)
        time.sleep(3)
        
        result = {
            'current_price': None,
            'original_price': None,
            'discount': None,
        }
        
        # === MODE DEBUG: Afficher tous les prix ===
        if debug:
            logger.debug("MODE DEBUG: Recherche de tous les prix sur la page...")
            try:
                all_price_elements = driver.find_elements(By.CSS_SELECTOR, 'span.a-offscreen')
                logger.debug(f"Trouvé {len(all_price_elements)} éléments avec classe 'a-offscreen':")
                for idx, elem in enumerate(all_price_elements[:10], 1):
                    text = elem.text.strip()
                    if not text:
                        text = elem.get_attribute('textContent')
                        if text:
                            text = text.strip()
                    if text:
                        logger.debug(f"  {idx}. {text}")
            except Exception as e:
                logger.debug(f"Erreur debug: {e}")
        
        # === RECHERCHE DU PRIX ACTUEL ===
        current_price_selectors = [
            (By.CLASS_NAME, 'a-price-whole'),
            (By.CSS_SELECTOR, '.a-price .a-offscreen'),
            (By.ID, 'priceblock_ourprice'),
            (By.ID, 'priceblock_dealprice'),
            (By.CSS_SELECTOR, 'span.a-price span.a-offscreen'),
            (By.XPATH, "//span[contains(@class, 'a-price')]//span[@class='a-offscreen']"),
            (By.CSS_SELECTOR, '#corePrice_feature_div .a-price .a-offscreen'),
            (By.CSS_SELECTOR, '#apex_desktop .a-price .a-offscreen'),
        ]
        
        for selector_type, selector_value in current_price_selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                price_text = element.text.strip()
                
                if not price_text:
                    price_text = element.get_attribute('textContent')
                    if price_text:
                        price_text = price_text.strip()
                
                if price_text and price_text != '':
                    result['current_price'] = price_text
                    if logger:
                        logger.info(f"Prix actuel trouvé: {price_text}")
                    break
                    
            except TimeoutException:
                continue
            except Exception:
                continue
        
        # === RECHERCHE DU PRIX ORIGINAL (BARRÉ) ===
        original_price_selectors = [
            (By.CSS_SELECTOR, '.basisPrice .a-price .a-offscreen'),
            (By.CSS_SELECTOR, 'span.basisPrice .a-price .a-offscreen'),
            (By.CSS_SELECTOR, '.basisPrice .a-price[data-a-strike="true"] .a-offscreen'),
            (By.CSS_SELECTOR, 'span.basisPrice .a-price[data-a-strike="true"] span.a-offscreen'),
            (By.CSS_SELECTOR, '.basisPrice span.a-offscreen'),
            (By.CSS_SELECTOR, 'span.basisPrice span.a-offscreen'),
            (By.CSS_SELECTOR, '.basisPrice .a-offscreen'),
            (By.CSS_SELECTOR, 'span.a-price.a-text-price span.a-offscreen'),
            (By.CSS_SELECTOR, '.a-text-price .a-offscreen'),
            (By.CSS_SELECTOR, 'span[data-a-strike="true"] .a-offscreen'),
            (By.XPATH, "//span[contains(@class, 'a-text-price')]//span[@class='a-offscreen']"),
            (By.CSS_SELECTOR, '#corePrice_feature_div .a-text-price .a-offscreen'),
            (By.XPATH, "//span[@class='a-price a-text-price']//span[@class='a-offscreen']"),
            (By.CSS_SELECTOR, '.a-section.a-spacing-small span.a-price.a-text-price span.a-offscreen'),
            (By.XPATH, "//span[contains(text(), 'Prix conseillé')]/following-sibling::span//span[@class='a-offscreen']"),
            (By.XPATH, "//span[contains(@class, 'basisPrice')]//span[@data-a-strike='true']//span[@class='a-offscreen']"),
            (By.XPATH, "//span[contains(@class, 'basisPrice')]//span[@class='a-offscreen']"),
        ]
        
        for selector_type, selector_value in original_price_selectors:
            try:
                if selector_type == By.CSS_SELECTOR:
                    elements = driver.find_elements(selector_type, selector_value)
                    if debug and elements and logger:
                        logger.debug(f"Testé: {selector_value} -> {len(elements)} élément(s) trouvé(s)")
                else:
                    elements = [driver.find_element(selector_type, selector_value)]
                    if debug and elements and logger:
                        logger.debug(f"Testé: {selector_value} -> élément trouvé")
                
                for element in elements:
                    original_text = element.text.strip()
                    
                    if not original_text:
                        original_text = element.get_attribute('textContent')
                        if original_text:
                            original_text = original_text.strip()
                    
                    if not original_text:
                        original_text = element.get_attribute('innerHTML')
                        if original_text:
                            original_text = original_text.strip()
                    
                    if debug and logger:
                        logger.debug(f"  Texte: '{original_text}' (prix actuel: '{result['current_price']}')")
                    
                    if original_text and original_text != '' and original_text != result['current_price']:
                        result['original_price'] = original_text
                        if logger:
                            logger.info(f"Prix original trouvé: {original_text} (sélecteur: {selector_value})")
                        break
                
                if result['original_price']:
                    break
                    
            except Exception as e:
                if debug and logger:
                    logger.debug(f"Testé: {selector_value} -> échec ({type(e).__name__})")
                continue
        
        # === RECHERCHE DU POURCENTAGE DE RÉDUCTION ===
        discount_selectors = [
            (By.CSS_SELECTOR, '.savingsPercentage'),
            (By.CSS_SELECTOR, 'span.savingPriceOverride'),
            (By.CSS_SELECTOR, '.a-badge-label'),
            (By.XPATH, "//span[contains(text(), '%') and contains(text(), '-')]"),
            (By.XPATH, "//span[@class='a-color-price' and contains(text(), '%')]"),
            (By.CSS_SELECTOR, 'span.a-size-large.a-color-price'),
        ]
        
        for selector_type, selector_value in discount_selectors:
            try:
                element = driver.find_element(selector_type, selector_value)
                discount_text = element.text.strip()
                
                if not discount_text:
                    discount_text = element.get_attribute('textContent')
                    if discount_text:
                        discount_text = discount_text.strip()
                
                if '%' in discount_text and '-' in discount_text:
                    result['discount'] = discount_text
                    if logger:
                        logger.info(f"Réduction trouvée: {discount_text}")
                    break
                    
            except Exception:
                continue
        
        # Si on a trouvé une réduction mais pas de prix original, chercher plus largement
        if result['discount'] and not result['original_price']:
            if logger:
                logger.warning("Réduction détectée mais prix original non trouvé. Recherche élargie...")
            try:
                all_prices = driver.find_elements(By.CSS_SELECTOR, 'span.a-offscreen')
                prices_text = []
                for p in all_prices:
                    text = p.text.strip()
                    if not text:
                        text = p.get_attribute('textContent')
                        if text:
                            text = text.strip()
                    if text and '€' in text:
                        prices_text.append(text)
                
                for price_text in prices_text:
                    if price_text != result['current_price'] and price_text:
                        result['original_price'] = price_text
                        if logger:
                            logger.info(f"Prix original trouvé (recherche élargie): {price_text}")
                        break
            except Exception:
                pass
        
        # Si aucun prix actuel trouvé, recherche de fallback
        if not result['current_price']:
            if logger:
                logger.warning("Aucun prix trouvé avec les sélecteurs standard.")
                logger.info("Recherche de tous les éléments contenant 'EUR' ou '€'...")
            
            page_source = driver.page_source
            prices_found = re.findall(r'(\d+[,\.]\d+\s*€|€\s*\d+[,\.]\d+|\d+[,\.]\d+\s*EUR)', page_source)
            
            if prices_found:
                if logger:
                    logger.info(f"Prix potentiels trouvés dans le HTML:")
                    for p in set(prices_found[:5]):
                        logger.info(f"  - {p}")
                result['current_price'] = prices_found[0]
        
        # Convertir en valeurs numériques
        prix_vente, devise = parse_price(result['current_price'])
        prix_base, _ = parse_price(result['original_price'])
        pourcentage_promo = parse_discount(result['discount'])
        
        # Si pas de devise détectée, utiliser € par défaut
        if not devise:
            devise = '€'
        
        return [prix_vente, devise, prix_base, pourcentage_promo]
            
    except Exception as e:
        if logger:
            logger.error(f"Erreur: {e}")
        return [None, None, None, None]
        
    finally:
        if driver:
            driver.quit()


def display_amazon_price(url, logger=None):
    """
    Affiche les résultats de la récupération du prix Amazon
    
    Args:
        url: URL de la page produit Amazon
        logger: Logger pour afficher les messages
    
    Returns:
        True si succès, False sinon
    """
    if logger:
        logger.info("=" * 60)
        logger.info("🔍 Scraper de prix Amazon avec Selenium")
        logger.info("=" * 60)
        logger.info(f"URL: {url}")
        logger.info("")
    
    prix_vente, devise, prix_base, pourcentage_promo = get_amazon_price(url, logger)
    
    if not prix_vente:
        if logger:
            logger.error("")
            logger.error("💡 Conseils:")
            logger.error("  - Vérifiez que ChromeDriver est installé")
            logger.error("  - L'article existe peut-être plus ou est indisponible")
            logger.error("  - Amazon peut bloquer les accès automatisés")
        return False
    
    if logger:
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 RÉSULTATS")
        logger.info("=" * 60)
        logger.info(f"")
        logger.info(f"💰 Prix actuel: {prix_vente:.2f} {devise}")
        
        if prix_base and prix_base > prix_vente:
            logger.info(f"🏷️  Prix original: {prix_base:.2f} {devise}")
            if pourcentage_promo:
                logger.info(f"🎉 Réduction: -{pourcentage_promo}%")
            logger.info("")
            logger.info("✨ Ce produit est EN PROMOTION ! ✨")
        else:
            logger.info("")
            logger.info("ℹ️  Pas de promotion détectée")
        
        logger.info("")
        logger.info("=" * 60)
    
    return True


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
  python %(prog)s https://www.amazon.fr/dp/B0BJQ7F16T --debug
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
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Mode debug: affiche tous les prix trouvés sur la page'
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
    
    # Configurer le logger
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Afficher les résultats
    success = display_amazon_price(url, logger)
    
    sys.exit(0 if success else 1)