"""
Travel Engine — item 10.
Distance de voyage (km) et décalage horaire entre le pays de l'équipe
et le stade du match. Un long voyage + grand décalage = légère pénalité.
"""
import math
from typing import Optional

# Capitale ou centre géographique de chaque pays qualifié (lat, lon)
TEAM_COORDS = {
    # CONMEBOL
    "Argentina":          (-34.6037, -58.3816),   # Buenos Aires
    "Brazil":             (-15.7801, -47.9292),   # Brasilia
    "Colombia":           (4.7110,   -74.0721),   # Bogota
    "Ecuador":            (-0.2295,  -78.5243),   # Quito
    "Uruguay":            (-34.9011, -56.1645),   # Montevideo
    "Paraguay":           (-25.2867, -57.6470),   # Asuncion
    # UEFA
    "Spain":              (40.4168,   -3.7038),   # Madrid
    "England":            (51.5074,   -0.1278),   # London
    "France":             (48.8566,    2.3522),   # Paris
    "Germany":            (52.5200,   13.4050),   # Berlin
    "Portugal":           (38.7167,   -9.1333),   # Lisbon
    "Netherlands":        (52.3702,    4.8952),   # Amsterdam
    "Belgium":            (50.8503,    4.3517),   # Brussels
    "Croatia":            (45.8150,   15.9819),   # Zagreb
    "Austria":            (48.2082,   16.3738),   # Vienna
    "Switzerland":        (46.9481,    7.4474),   # Bern
    "Denmark":            (55.6761,   12.5683),   # Copenhagen
    "Turkey":             (39.9334,   32.8597),   # Ankara
    "Serbia":             (44.8176,   20.4633),   # Belgrade
    "Scotland":           (55.9533,   -3.1883),   # Edinburgh
    "Norway":             (59.9139,   10.7522),   # Oslo
    "Sweden":             (59.3293,   18.0686),   # Stockholm
    "Bosnia-Herzegovina": (43.8476,   18.3564),   # Sarajevo
    "Czechia":            (50.0755,   14.4378),   # Prague
    # CONCACAF
    "USA":                (38.8951,  -77.0364),   # Washington DC
    "Mexico":             (19.4326,  -99.1332),   # Mexico City
    "Canada":             (45.4215,  -75.6972),   # Ottawa
    "Panama":             (8.9936,   -79.5197),   # Panama City
    "Haiti":              (18.5944,  -72.3074),   # Port-au-Prince
    "Jamaica":            (17.9970,  -76.7936),   # Kingston
    # CAF
    "Morocco":            (33.9716,   -6.8498),   # Rabat
    "Senegal":            (14.7167,  -17.4677),   # Dakar
    "Nigeria":            (9.0765,    7.3986),   # Abuja
    "Egypt":              (30.0444,   31.2357),   # Cairo
    "Ivory Coast":        (5.3600,   -4.0083),   # Abidjan
    "Cameroon":           (3.8480,   11.5021),   # Yaounde
    "South Africa":       (-25.7461,  28.1881),   # Pretoria
    "DR Congo":           (-4.3217,   15.3222),   # Kinshasa
    "Algeria":            (36.7372,    3.0865),   # Algiers
    "Tunisia":            (36.8190,   10.1658),   # Tunis
    "Ghana":              (5.6037,   -0.1870),   # Accra
    "Cape Verde":         (14.9315,  -23.5133),   # Praia
    # AFC
    "Japan":              (35.6762,  139.6503),   # Tokyo
    "South Korea":        (37.5665,  126.9780),   # Seoul
    "Iran":               (35.6892,   51.3890),   # Tehran
    "Australia":          (-35.2809, 149.1300),   # Canberra
    "Saudi Arabia":       (24.6877,   46.7219),   # Riyadh
    "Uzbekistan":         (41.2995,   69.2401),   # Tashkent
    "Jordan":             (31.9539,   35.9106),   # Amman
    "Iraq":               (33.3406,   44.4009),   # Baghdad
    "Qatar":              (25.2854,   51.5310),   # Doha
    # OFC
    "New Zealand":        (-41.2865,  174.7762),  # Wellington
    # Autres
    "Curaçao":            (12.1696,  -68.9900),   # Willemstad
}

# Stades WC 2026 (lat, lon, timezone UTC offset)
STADIUM_DATA = {
    "MetLife Stadium":          (40.8128,  -74.0742,  -4),  # New York/NJ
    "AT&T Stadium":             (32.7473,  -97.0945,  -5),  # Dallas
    "SoFi Stadium":             (33.9534, -118.3392,  -7),  # Los Angeles
    "Rose Bowl":                (34.1613, -118.1676,  -7),  # Pasadena
    "Levi's Stadium":           (37.4033, -121.9694,  -7),  # San Francisco
    "BC Place":                 (49.2768, -123.1116,  -7),  # Vancouver
    "Estadio Azteca":           (19.3029,  -99.1505,  -5),  # Mexico City
    "Estadio Akron":            (20.6893, -103.4673,  -5),  # Guadalajara
    "Hard Rock Stadium":        (25.9580,  -80.2390,  -4),  # Miami
    "NRG Stadium":              (29.6847,  -95.4107,  -5),  # Houston
    "Gillette Stadium":         (42.0909,  -71.2643,  -4),  # Boston
    "Arrowhead Stadium":        (39.0489,  -94.4839,  -5),  # Kansas City
    "Lumen Field":              (47.5952, -122.3316,  -7),  # Seattle
    "Mercedes-Benz Stadium":    (33.7553,  -84.4006,  -4),  # Atlanta
    "Lincoln Financial Field":  (39.9008,  -75.1675,  -4),  # Philadelphia
    "BMO Field":                (43.6333,  -79.4186,  -4),  # Toronto
    "Estadio BBVA":             (25.6693, -100.3117,  -5),  # Monterrey
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en km entre deux points GPS."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    return round(2 * R * math.asin(math.sqrt(a)), 0)


def get_travel_stats(team: str, stadium: str) -> dict:
    """
    Retourne distance de voyage et impact estimé sur la performance.
    """
    team_c  = TEAM_COORDS.get(team)
    stad_d  = STADIUM_DATA.get(stadium)

    if not team_c or not stad_d:
        return {
            "team": team, "stadium": stadium,
            "travel_km": None, "tz_offset_h": None,
            "travel_fatigue_mult": 1.0,
        }

    slat, slon, stz = stad_d
    tlat, tlon      = team_c

    km = _haversine(tlat, tlon, slat, slon)

    # Timezone offset de l'équipe (approximation depuis la longitude)
    team_tz  = round(tlon / 15)
    delta_tz = abs(stz - team_tz)

    # Multiplicateur de performance (basé sur recherches sportives)
    # > 8000 km ou > 8h de décalage : légère pénalité
    if km > 15000:
        mult = 0.96
        level = "severe"
    elif km > 10000:
        mult = 0.97
        level = "high"
    elif km > 8000 or delta_tz >= 8:
        mult = 0.985
        level = "moderate"
    elif km > 5000 or delta_tz >= 5:
        mult = 0.995
        level = "low"
    else:
        mult = 1.0
        level = "minimal"

    return {
        "team":                 team,
        "stadium":              stadium,
        "travel_km":            km,
        "tz_offset_h":          delta_tz,
        "travel_level":         level,
        "travel_fatigue_mult":  mult,
    }
