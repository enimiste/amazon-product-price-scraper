# Scruper du prix d'un produit sur Amazon

## Développement en local :
```shell
python -m venv venv.nosync
source venv.nosync/bin/activate
pip install -r requirements.txt
```

## Exécution :
```shell
(venv.nosync) % python ./main.py --help                                    
usage: main.py [-h] [--url URL_FLAG] [url]

Récupère le prix d'un article Amazon

positional arguments:
  url             URL de la page produit Amazon

options:
  -h, --help      show this help message and exit
  --url URL_FLAG  URL de la page produit Amazon (alternative)

Exemples d'utilisation:
  python main.py https://www.amazon.fr/dp/B0DCBB2YTR
  python main.py "https://www.amazon.fr/dp/B0DCBB2YTR?th=1"
  python main.py --url https://www.amazon.com/dp/B08N5WRWNW

(venv.nosync) % python ./main.py "https://www.amazon.fr/dp/B0DCBB2YTR?th=1"
URL: https://www.amazon.fr/dp/B0DCBB2YTR?th=1

Chargement de la page...
✓ Prix trouvé avec le sélecteur: a-price-whole

💰 Prix final: 99
```

## En cas d'erreur avec webdrive :
```shell
# Supprimer le cache corrompu
rm -rf ~/.wdm
# Réinstaller
pip install --upgrade webdriver-manager
```