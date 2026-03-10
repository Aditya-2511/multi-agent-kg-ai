import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# ── RapidAPI ──────────────────────────────────────────────────────────────────
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# ── Train API (fixed constants — not environment-specific) ────────────────────
TRAIN_RAPIDAPI_HOST = "irctc1.p.rapidapi.com"
TRAIN_BASE_URL      = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"

# ── GraphDB ───────────────────────────────────────────────────────────────────
GRAPHDB_ENDPOINT        = os.getenv("GRAPHDB_ENDPOINT",        "http://localhost:7200/repositories/company_kg")
GRAPHDB_UPDATE_ENDPOINT = os.getenv("GRAPHDB_UPDATE_ENDPOINT", "http://localhost:7200/repositories/company_kg/statements")

# ── Station code lookup ───────────────────────────────────────────────────────
STATION_CODES: dict[str, str] = {
    # Mumbai
    "mumbai":              "MMCT",
    "mumbai central":      "MMCT",
    "mumbai csmt":         "CSMT",
    "cst":                 "CSMT",
    "mumbai bandra":       "BDTS",
    "bandra":              "BDTS",
    # Delhi
    "delhi":               "NDLS",
    "new delhi":           "NDLS",
    "hazrat nizamuddin":   "NZM",
    "nizamuddin":          "NZM",
    "delhi sarai rohilla": "DEE",
    # Rajasthan
    "ajmer":               "AII",
    "jaipur":              "JP",
    "jodhpur":             "JU",
    "udaipur":             "UDZ",
    "kota":                "KOTA",
    # Maharashtra
    "pune":                "PUNE",
    "nagpur":              "NGP",
    "nashik":              "NK",
    "borivali":            "BVI",
    "kalyan":              "KYN",
    "thane":               "TNA",
    "panvel":              "PNVL",
    "vasai":               "BSR",
    "dadar":               "DR",
    # North India
    "amritsar":            "ASR",
    "haridwar":            "HW",
    "katra":               "SVDK",
    "chandigarh":          "CDG",
    "lucknow":             "LKO",
    "varanasi":            "BSB",
    "agra":                "AGC",
    "mathura":             "MTJ",
    # South India
    "bangalore":           "SBC",
    "bengaluru":           "SBC",
    "chennai":             "MAS",
    "hyderabad":           "HYB",
    "kochi":               "ERS",
    "ernakulam":           "ERS",
    "trivandrum":          "TVC",
    # East India
    "kolkata":             "KOAA",
    "howrah":              "HWH",
    "patna":               "PNBE",
    "bhubaneswar":         "BBS",
    # West India
    "ahmedabad":           "ADI",
    "surat":               "ST",
    "vadodara":            "BRC",
}