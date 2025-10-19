import requests
from bs4 import BeautifulSoup
import re

def get_amazon_price(url):
    """
    Récupère le prix d'un article Amazon
    """
    # Headers pour simuler un navigateur
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
    }
    
    try:
        # Requête GET vers la page Amazon
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Différentes méthodes pour trouver le prix
        price = None
        
        # Méthode 1: Prix principal
        price_whole = soup.find('span', {'class': 'a-price-whole'})
        price_fraction = soup.find('span', {'class': 'a-price-fraction'})
        print(["Méthode 1", price_whole is not None, price_fraction is not None])

        if price_whole and price_fraction:
            price = f"{price_whole.text.strip()}{price_fraction.text.strip()}"
        
        # Méthode 2: Prix dans l'offre
        if not price:
            price_span = soup.find('span', {'class': 'a-offscreen'})
            print(["Méthode 2", price_span is not None])
            if price_span:
                price = price_span.text.strip()
        
        # Méthode 3: Recherche par ID
        if not price:
            price_elem = soup.find(id='priceblock_ourprice')
            print(["Méthode 3", price_elem is not None])
            if price_elem:
                price = price_elem.text.strip()
        
        # Méthode 4: Prix deal
        if not price:
            price_elem = soup.find(id='priceblock_dealprice')
            print(["Méthode 4", price_elem is not None])
            if price_elem:
                price = price_elem.text.strip()
        
        if price:
            # Nettoyer le prix
            price = price.replace('\xa0', ' ').replace(',', '.')
            print(f"Prix trouvé: {price}")
            return price
        else:
            print("Prix non trouvé sur la page")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête: {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return None

if __name__ == "__main__":
    # URL de l'article Amazon
    url = "https://www.amazon.fr/dp/B0DCBB2YTR?th=1"
    
    print(f"Récupération du prix pour: {url}")
    print("-" * 50)
    
    price = get_amazon_price(url)
    
    if not price:
        print("\n⚠️  Impossible de récupérer le prix.")
        print("Note: Amazon peut bloquer les scrapers. Essayez d'attendre quelques instants.")