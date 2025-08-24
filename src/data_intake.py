import requests
import pandas as pd
import random
from io import StringIO

from utils.config import THE_ODDS_API_KEY, API_FOOTBALL_KEY

API_FOOTBALL_HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

# === League IDs (API-Football) ===
LEAGUE_IDS = {
    "nba": 12,
    "nfl": 1,
    "mlb": 3,
    "nhl": 4,
    "mma": 5
}

# === Fetch from API-Football ===
def fetch_api_football(league_id):
    url = f"https://v3.football.api-sports.io/odds"
    params = {"league": league_id, "season": "2024"}  # Adjust season as needed
    try:
        response = requests.get(url, headers=API_FOOTBALL_HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            print(f"[Data Intake] Fetched odds from API-Football (league {league_id}).")
            return response.json()
        else:
            print(f"[Data Intake] API-Football error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[Data Intake] API-Football request failed: {e}")
        return None

# === Fetch from The Odds API ===
def fetch_odds_api(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {"regions": "us", "markets": "spreads,totals", "apiKey": THE_ODDS_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print(f"[Data Intake] Fetched odds from The Odds API ({sport_key}).")
            return response.json()
        else:
            print(f"[Data Intake] Odds API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[Data Intake] Odds API request failed: {e}")
        return None

# === Scrape DFF Projections ===
def scrape_dff_projections():
    url = "https://dailyfantasyfuel.com/nba/projections/csv"
    try:
        response = requests.get(url, timeout=10)
        decoded = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(decoded), on_bad_lines='skip')
        df = df[['Player', 'Proj']].rename(columns={'Player': 'player', 'Proj': 'proj_points'})
        print("[Data Intake] Scraped DFF projections.")
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"[Data Intake] DFF scraping failed: {e}")
        return []

# === Generate Metrics from Data ===
def generate_metrics_from_data():
    print("[Data Intake] Starting to generate metrics...")  # Debug line
    # Try API-Football for each league
    for sport, league_id in LEAGUE_IDS.items():
        data = fetch_api_football(league_id)
        if data:
            print(f"[Data Intake] Data fetched for {sport} - {league_id}")  # Debug line
            return process_odds_into_metrics(data)

    # Fallback to Odds API
    for sport_key in ["basketball_nba", "americanfootball_nfl", "baseball_mlb"]:
        data = fetch_odds_api(sport_key)
        if data:
            print(f"[Data Intake] Data fetched for {sport_key}")  # Debug line
            return process_odds_into_metrics(data)

    # Fallback to DFF scraping
    projections = scrape_dff_projections()
    if projections:
        print(f"[Data Intake] Data fetched from DFF projections")  # Debug line
        return process_projections_into_metrics(projections)

    # Final fallback to simulated metrics
    print("[Data Intake] All data sources failed. Using simulated metrics.")  # Debug line
    return simulate_metrics()

# === Process Odds into Metrics ===
def process_odds_into_metrics(data):
    # Placeholder logic
    metrics = {
        "profitability": random.uniform(10, 100),
        "variance": random.uniform(0.2, 0.5),
        "consistency": random.uniform(0.7, 1.0),
        "drawdown": random.uniform(0.05, 0.15),
        "sharpe_ratio": random.uniform(1.0, 2.0),
        "edge_discovery": random.uniform(0.1, 0.5),
        "deployment_win_rate": random.uniform(0.6, 0.9)
    }
    print(f"[Data Intake] Metrics generated from odds: {metrics}")
    return metrics

# === Process Projections into Metrics ===
def process_projections_into_metrics(projections):
    avg_proj = sum(p['proj_points'] for p in projections) / len(projections)
    metrics = {
        "profitability": avg_proj * random.uniform(0.5, 1.5),
        "variance": random.uniform(0.2, 0.5),
        "consistency": random.uniform(0.7, 1.0),
        "drawdown": random.uniform(0.05, 0.15),
        "sharpe_ratio": random.uniform(1.0, 2.0),
        "edge_discovery": random.uniform(0.1, 0.5),
        "deployment_win_rate": random.uniform(0.6, 0.9)
    }
    print(f"[Data Intake] Metrics generated from projections: {metrics}")
    return metrics

# === Simulated Metrics ===
def simulate_metrics():
    metrics = {
        "profitability": random.uniform(10, 100),
        "variance": random.uniform(0.2, 0.5),
        "consistency": random.uniform(0.7, 1.0),
        "drawdown": random.uniform(0.05, 0.15),
        "sharpe_ratio": random.uniform(1.0, 2.0),
        "edge_discovery": random.uniform(0.1, 0.5),
        "deployment_win_rate": random.uniform(0.6, 0.9)
    }
    print(f"[Data Intake] Simulated metrics: {metrics}")
    return metrics

# === Standalone Test ===
if __name__ == "__main__":
    generate_metrics_from_data()  # Directly call the function to test the flow
