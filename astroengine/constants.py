"""Static tables. Every table names its source; contested ones live in config.py."""

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Primary (Parashari) sign lords. Scorpio/Aquarius co-lords (Ketu/Rahu) are
# handled explicitly where a technique uses them (Jaimini).
SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
             "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
CO_LORD = {7: "Ketu", 10: "Rahu"}

QUALITY = ["movable", "fixed", "dual"]          # index = sign % 3
ELEMENT = ["fire", "earth", "air", "water"]     # index = sign % 4

# Jaimini footedness: savya (odd-footed) signs. Everything else is apasavya.
SAVYA = {0, 1, 2, 6, 7, 8}

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NODES = ["Rahu", "Ketu"]
PLANETS = GRAHAS + NODES
OUTER = ["Uranus", "Neptune", "Pluto"]

WEEKDAY_LORD = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]  # Sunday=0
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

NAK_SPAN = 360.0 / 27.0
PADA_SPAN = NAK_SPAN / 4.0

# name, Vimshottari lord, deity, gana, yoni, nadi
NAKSHATRAS = [
    ("Ashwini", "Ketu", "Ashvini Kumaras", "Deva", "Horse", "Adi"),
    ("Bharani", "Venus", "Yama", "Manushya", "Elephant", "Madhya"),
    ("Krittika", "Sun", "Agni", "Rakshasa", "Sheep", "Antya"),
    ("Rohini", "Moon", "Prajapati", "Manushya", "Serpent", "Antya"),
    ("Mrigashira", "Mars", "Soma", "Deva", "Serpent", "Madhya"),
    ("Ardra", "Rahu", "Rudra", "Manushya", "Dog", "Adi"),
    ("Punarvasu", "Jupiter", "Aditi", "Deva", "Cat", "Adi"),
    ("Pushya", "Saturn", "Brihaspati", "Deva", "Sheep", "Madhya"),
    ("Ashlesha", "Mercury", "Sarpas", "Rakshasa", "Cat", "Antya"),
    ("Magha", "Ketu", "Pitris", "Rakshasa", "Rat", "Antya"),
    ("Purva Phalguni", "Venus", "Bhaga", "Manushya", "Rat", "Madhya"),
    ("Uttara Phalguni", "Sun", "Aryaman", "Manushya", "Cow", "Adi"),
    ("Hasta", "Moon", "Savitr", "Deva", "Buffalo", "Adi"),
    ("Chitra", "Mars", "Tvashtr", "Rakshasa", "Tiger", "Madhya"),
    ("Swati", "Rahu", "Vayu", "Deva", "Buffalo", "Antya"),
    ("Vishakha", "Jupiter", "Indragni", "Rakshasa", "Tiger", "Antya"),
    ("Anuradha", "Saturn", "Mitra", "Deva", "Deer", "Madhya"),
    ("Jyeshtha", "Mercury", "Indra", "Rakshasa", "Deer", "Adi"),
    ("Mula", "Ketu", "Nirriti", "Rakshasa", "Dog", "Adi"),
    ("Purva Ashadha", "Venus", "Apas", "Manushya", "Monkey", "Madhya"),
    ("Uttara Ashadha", "Sun", "Vishvedevas", "Manushya", "Mongoose", "Antya"),
    ("Shravana", "Moon", "Vishnu", "Deva", "Monkey", "Antya"),
    ("Dhanishta", "Mars", "Vasus", "Rakshasa", "Lion", "Madhya"),
    ("Shatabhisha", "Rahu", "Varuna", "Rakshasa", "Horse", "Adi"),
    ("Purva Bhadrapada", "Jupiter", "Aja Ekapada", "Manushya", "Lion", "Adi"),
    ("Uttara Bhadrapada", "Saturn", "Ahir Budhnya", "Manushya", "Cow", "Madhya"),
    ("Revati", "Mercury", "Pushan", "Deva", "Elephant", "Antya"),
]

VIM_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIM_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
             "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

# Deep exaltation points (sidereal longitude). Debilitation = +180.
EXALT_POINT = {"Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
               "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0}

OWN_SIGNS = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
             "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}

# Moolatrikona sign and degree range (BPHS ch.3 as commonly tabulated).
MOOLATRIKONA = {"Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12),
                "Mercury": (5, 15, 20), "Jupiter": (8, 0, 10),
                "Venus": (6, 0, 15), "Saturn": (10, 0, 20)}

# Naisargika (natural) relationships, BPHS ch.3.
NATURAL_FRIENDS = {
    "Sun": (["Moon", "Mars", "Jupiter"], ["Mercury"], ["Venus", "Saturn"]),
    "Moon": (["Sun", "Mercury"], ["Mars", "Jupiter", "Venus", "Saturn"], []),
    "Mars": (["Sun", "Moon", "Jupiter"], ["Venus", "Saturn"], ["Mercury"]),
    "Mercury": (["Sun", "Venus"], ["Mars", "Jupiter", "Saturn"], ["Moon"]),
    "Jupiter": (["Sun", "Moon", "Mars"], ["Saturn"], ["Mercury", "Venus"]),
    "Venus": (["Mercury", "Saturn"], ["Mars", "Jupiter"], ["Sun", "Moon"]),
    "Saturn": (["Mercury", "Venus"], ["Jupiter"], ["Sun", "Moon", "Mars"]),
    # Nodes: not in BPHS's table; the commonly used modern convention.
    "Rahu": (["Mercury", "Venus", "Saturn"], ["Jupiter"], ["Sun", "Moon", "Mars"]),
    "Ketu": (["Mercury", "Venus", "Saturn"], ["Jupiter"], ["Sun", "Moon", "Mars"]),
}

COMBUSTION_ORB = {"Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
                  "Venus": 10.0, "Saturn": 15.0}
COMBUSTION_ORB_RETRO = {"Mercury": 12.0, "Venus": 8.0}

MEAN_DAILY_MOTION = {"Sun": 0.9856, "Moon": 13.1764, "Mars": 0.5240,
                     "Mercury": 0.9856, "Jupiter": 0.0831, "Venus": 0.9856,
                     "Saturn": 0.0335, "Rahu": -0.0530, "Ketu": -0.0530}

TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
          "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
          "Trayodashi", "Chaturdashi"]

YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
         "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
         "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
         "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]

KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]

# Amanta month named from the sidereal sign of the Sun at the opening new moon.
MASA_BY_SUN_SIGN = ["Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
                    "Ashvina", "Kartika", "Margashirsha", "Pausha", "Magha",
                    "Phalguna", "Chaitra"]

# 1/8 day-portion (1-based) ruled by Rahu / Gulika / Yamaganda kalam, Sunday first.
RAHU_KALAM_PART = [8, 2, 7, 5, 6, 4, 3]
GULIKA_KALAM_PART = [7, 6, 5, 4, 3, 2, 1]
YAMAGANDA_PART = [5, 4, 3, 2, 1, 7, 6]

# BPHS ch.6 Shashtiamsa deities, odd signs in this order, even signs reversed.
D60_DEITIES = [
    "Ghora", "Rakshasa", "Deva", "Kubera", "Yaksha", "Kinnara", "Bhrashta", "Kulaghna",
    "Garala", "Vahni", "Maya", "Purishaka", "Apampati", "Marutvan", "Kaala", "Sarpa",
    "Amrita", "Indu", "Mridu", "Komala", "Heramba", "Brahma", "Vishnu", "Maheshvara",
    "Deva", "Ardra", "Kalinasha", "Kshitisha", "Kamalakara", "Gulika", "Mrityu", "Kaala",
    "Davagni", "Ghora", "Yama", "Kantaka", "Sudha", "Amrita", "Purnachandra", "Vishadagdha",
    "Kulanasha", "Vamshakshaya", "Utpata", "Kaala", "Saumya", "Komala", "Sheetala",
    "Karaladamshtra", "Chandramukhi", "Praveena", "Kalapavaka", "Dandayudha", "Nirmala",
    "Saumya", "Krura", "Atisheetala", "Amrita", "Payodhi", "Bhramana", "Chandrarekha",
]
assert len(D60_DEITIES) == 60

# Ashtakoota varna / vashya of the Moon sign (used by matching software).
# Fire signs Kshatriya, earth Vaishya, air Shudra, water Brahmin.
VARNA = ["Kshatriya", "Vaishya", "Shudra", "Brahmin"]   # index = sign % 4

NAISARGIKA_BALA = {"Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
                   "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57}
SHADBALA_REQUIRED_RUPAS = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
                           "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0}

TARA_NAMES = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana",
              "Naidhana", "Mitra", "Parama Mitra"]
