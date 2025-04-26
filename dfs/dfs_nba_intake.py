# === DFS NBA Intake: Multi-Source Stitch with Reflexive Loop ===
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# === Source 1: Rotowire Scrape ===
def scrape_rotowire_nba():
    try:
        url = "https://www.rotowire.com/basketball/nba-lineups.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = []
        for row in soup.select('div.lineup__player'):
            player = row.select_one('a.lineup__player-link').text.strip()
            status = row.select_one('span.lineup__player-status')
            status = status.text.strip() if status else "Active"
            data.append({'source': 'Rotowire', 'player': player, 'status': status})
        return data
    except Exception as e:
        raise Exception("Rotowire scrape failed")

# === Source 2: Balldontlie API ===
def fetch_balldontlie():
    try:
        url = "https://api.balldontlie.io/v1/players?per_page=100"
        headers = {'Authorization': 'Bearer 770462d2-d911-4799-90d0-8d702b918dc3'}
        response = requests.get(url, headers=headers)
        players = response.json().get('data', [])
        return [{'source': 'Balldontlie', 'player': p['first_name'] + ' ' + p['last_name'], 'team': p['team']['full_name']} for p in players]
    except Exception as e:
        raise Exception("Balldontlie API failed")

# === Source 3: OddsAPI ===
def fetch_oddsapi_players():
    try:
        url = "https://odds.p.rapidapi.com/v4/sports/basketball_nba/odds"
        headers = {
            "X-RapidAPI-Key": "5a542f6e63msh4e7a65adf5675c4p14a13ajsn2e0c94b3e217",
            "X-RapidAPI-Host": "odds.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        games = response.json()
        data = []
        for game in games:
            for team in game.get('teams', []):
                data.append({'source': 'OddsAPI', 'team': team})
        return data
    except Exception as e:
        raise Exception("OddsAPI failed")

# === Stitch & Fallback ===
def get_nba_player_data():
    merged_data = []
    try:
        print("Trying Rotowire scrape...")
        merged_data += scrape_rotowire_nba()
    except Exception as e:
        print(f"scrape_rotowire_nba failed: {e}")
    try:
        print("Trying Balldontlie API...")
        merged_data += fetch_balldontlie()
    except Exception as e:
        print(f"fetch_balldontlie failed: {e}")
    try:
        print("Trying OddsAPI fallback...")
        merged_data += fetch_oddsapi_players()
    except Exception as e:
        print(f"fetch_oddsapi_players failed: {e}")
    return merged_data

# === Evolution Log ===
def log_failure():
    with open("evolution_log.txt", "a") as f:
        f.write(f"[{datetime.now()}] All sources failed\n")

# === Reflexive Loop ===
if __name__ == "__main__":
    while True:
        print("Starting DFS NBA Intake...")
        player_data = get_nba_player_data()
        if player_data:
            print(f"Data pull successful. Entries: {len(player_data)}")
            for entry in player_data:
                print(entry)
        else:
            print("All sources failed. Logging failure...")
            log_failure()
        print("Sleeping for 15 minutes...")
        time.sleep(60 * 15)
