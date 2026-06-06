"""
Transfermarkt — blessures, suspensions et valeur des effectifs.
Page cible : /verletzungen/verein/{id}  (injuries tracker)
Utilise requests avec headers navigateur.
"""
import re
import requests
import time
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.transfermarkt.com/",
}

# Slug TM → (slug, verein_id)
# Pour obtenir l'ID : voir l'URL de la page TM de l'équipe nationale
TEAM_DATA = {
    # CONMEBOL
    "Argentina":          ("argentinien",           3468),
    "Brazil":             ("brasilien",              3439),
    "Colombia":           ("kolumbien",              3816),
    "Ecuador":            ("ecuador",                3754),
    "Uruguay":            ("uruguay",                3333),
    "Paraguay":           ("paraguay",               3765),
    # UEFA
    "Spain":              ("spanien",                3375),
    "England":            ("england",                3513),
    "France":             ("frankreich",             3377),
    "Germany":            ("deutschland",            3376),
    "Portugal":           ("portugal",               3462),
    "Netherlands":        ("niederlande",            3378),
    "Belgium":            ("belgien",                3382),
    "Croatia":            ("kroatien",               3555),
    "Austria":            ("oesterreich",            3384),
    "Switzerland":        ("schweiz",                3387),
    "Denmark":            ("daenemark",              3389),
    "Turkey":             ("tuerkei",                3403),
    "Serbia":             ("serbien",                3447),
    "Scotland":           ("schottland",             3515),
    "Norway":             ("norwegen",               3394),
    "Sweden":             ("schweden",               3395),
    "Bosnia-Herzegovina": ("bosnien-herzegowina",    3501),
    "Czechia":            ("tschechien",             3384),
    # CONCACAF
    "USA":                ("vereinigte-staaten",     3505),
    "Mexico":             ("mexiko",                 3486),
    "Canada":             ("kanada",                 3508),
    "Panama":             ("panama",                 3491),
    "Haiti":              ("haiti",                  3496),
    "Jamaica":            ("jamaika",                3524),
    # CAF
    "Morocco":            ("marokko",                3453),
    "Senegal":            ("senegal",                3463),
    "Nigeria":            ("nigeria",                3456),
    "Egypt":              ("aegypten",               3451),
    "Ivory Coast":        ("elfenbeinkueste",        3452),
    "Cameroon":           ("kamerun",                3455),
    "South Africa":       ("suedafrika",             3461),
    "DR Congo":           ("demokratische-republik-kongo", 11505),
    "Algeria":            ("algerien",               3450),
    "Tunisia":            ("tunesien",               3464),
    "Ghana":              ("ghana",                  3454),
    "Cape Verde":         ("kap-verde",              8695),
    # AFC
    "Japan":              ("japan",                  3417),
    "South Korea":        ("suedkorea",              3416),
    "Iran":               ("iran",                   3426),
    "Australia":          ("australien",             3435),
    "Saudi Arabia":       ("saudi-arabien",          3432),
    "Uzbekistan":         ("usbekistan",             6752),
    "Jordan":             ("jordanien",              9949),
    "Iraq":               ("irak",                   3425),
    "Qatar":              ("katar",                  13664),
    # OFC
    "New Zealand":        ("neuseeland",             3448),
    # Autres
    "Curaçao":            ("curacao",                14036),
    "South Africa":       ("suedafrika",             3461),
}

# Liste des joueurs stars dont l'absence change significativement les probas
STAR_PLAYERS = {
    "France":      ["Mbappé", "Griezmann", "Camavinga", "Tchouaméni"],
    "Brazil":      ["Vinicius", "Rodrygo", "Paquetá", "Militão"],
    "Argentina":   ["Messi", "Di María", "De Paul", "Martínez"],
    "England":     ["Bellingham", "Kane", "Saka", "Foden"],
    "Spain":       ["Pedri", "Yamal", "Morata", "Rodri"],
    "Germany":     ["Musiala", "Kroos", "Gnabry", "Müller"],
    "Portugal":    ["Ronaldo", "Bruno", "Leão", "Cancelo"],
    "Netherlands": ["Van Dijk", "Depay", "Gakpo", "De Jong"],
    "Morocco":     ["En-Nesyri", "Ziyech", "Amrabat", "Hakimi"],
    "Japan":       ["Mitoma", "Doan", "Kubo", "Endo"],
}

BASE_URL = "https://www.transfermarkt.com/{slug}/verletzungen/verein/{id}"
SQUAD_URL = "https://www.transfermarkt.com/{slug}/kader/verein/{id}"

_CACHE: dict = {}


def _fetch(url: str) -> Optional[str]:
    try:
        time.sleep(1.2)
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None


def _parse_injuries(html: str, team: str) -> dict:
    """
    Parse la page injuries de Transfermarkt.
    Cherche les tableaux de blessés/suspendus.
    """
    d: dict = {"team": team, "source": "transfermarkt"}

    # Noms des joueurs blessés (dans les <td> de la table injuries)
    # Pattern: lien vers le profil joueur contenant le nom
    player_links = re.findall(
        r'href="/[^"]+/profil/spieler/\d+"[^>]*>\s*([^<]+?)\s*<',
        html, re.IGNORECASE
    )
    # Déduplique et nettoie
    players_seen = set()
    injured = []
    for name in player_links:
        name = name.strip()
        if len(name) > 3 and name not in players_seen:
            players_seen.add(name)
            injured.append(name)

    d["injured_players"] = injured[:10]   # max 10 pour éviter le bruit
    d["n_injured"] = len(injured)

    # Retours prévus (dates)
    return_dates = re.findall(
        r'(\d{1,2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        html, re.IGNORECASE
    )
    d["return_dates"] = return_dates[:5]

    # Check si une star est blessée
    stars = STAR_PLAYERS.get(team, [])
    html_lower = html.lower()
    stars_injured = [s for s in stars if s.lower() in html_lower]
    d["star_injured"] = len(stars_injured) > 0
    d["stars_injured_names"] = stars_injured

    return d


def _parse_squad_value(html: str, team: str) -> dict:
    """Parse la valeur marchande totale du squad depuis la page kader."""
    d: dict = {}

    # Total market value
    m = re.search(
        r'(?:Total market value|Gesamtmarktwert)[^\d€]*([\d,.]+\s*(?:bn|m|k|Mio|Tsd)?\s*€?)',
        html, re.IGNORECASE
    )
    if m:
        raw = m.group(1).strip()
        # Normalise
        num_m = re.search(r'([\d.,]+)', raw)
        unit_m = re.search(r'(bn|m|Mio|k|Tsd)', raw, re.IGNORECASE)
        if num_m:
            num = float(num_m.group(1).replace(",", "."))
            unit = (unit_m.group(1).lower() if unit_m else "").lower()
            if unit in ("bn",):
                d["squad_value_eur_m"] = round(num * 1000, 1)
            elif unit in ("m", "mio"):
                d["squad_value_eur_m"] = round(num, 1)
            elif unit in ("k", "tsd"):
                d["squad_value_eur_m"] = round(num / 1000, 2)
            else:
                d["squad_value_eur_m"] = round(num, 1)

    # Nombre de joueurs
    count = re.findall(r'\|\s*(?:GK|CB|RB|LB|CM|CAM|CDM|RW|LW|CF|ST|DF|MF|FW|ATT)\s*\|', html)
    d["squad_size"] = len(count) if count else None

    return d


def get_injuries(team: str) -> dict:
    """
    Retourne les blessures/suspensions pour une équipe nationale.
    """
    if team in _CACHE:
        return _CACHE[team]

    team_info = TEAM_DATA.get(team)
    if not team_info:
        result = {"team": team, "source": "transfermarkt", "error": "team_not_supported",
                  "injured_players": [], "star_injured": False, "n_injured": 0}
        _CACHE[team] = result
        return result

    slug, vid = team_info
    result: dict = {"team": team, "source": "transfermarkt"}

    # 1. Page blessures
    url = BASE_URL.format(slug=slug, id=vid)
    html = _fetch(url)
    if html:
        injury_data = _parse_injuries(html, team)
        result.update(injury_data)
    else:
        result["error"] = "fetch_failed"
        result["injured_players"] = []
        result["star_injured"] = False
        result["n_injured"] = 0

    # 2. Page squad (valeur)
    url2 = SQUAD_URL.format(slug=slug, id=vid)
    html2 = _fetch(url2)
    if html2:
        squad_data = _parse_squad_value(html2, team)
        result.update(squad_data)

    _CACHE[team] = result
    return result


def get_both(home: str, away: str) -> tuple[dict, dict]:
    h = get_injuries(home)
    a = get_injuries(away)
    return h, a
