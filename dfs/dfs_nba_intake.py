import requests
from bs4 import BeautifulSoup
import csv
import random
from datetime import datetime
import json
import os
import time

print("Boot sequence start...")

SALARY_CAP = 50000
POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']
CSV_PATH = '/home/zcg123/jarvisprime/JarvisPrime/data/csv_sources/'
SALARY_LOG_PATH = '/home/zcg123/jarvisprime/JarvisPrime/data/salary_logs/'

os.makedirs(SALARY_LOG_PATH, exist_ok=True)

# === Slate Scrapers ===
def get_espn_slate():
    print("\nScraping ESPN for today's slate...")
    try:
        url = "https://www.espn.com/nba/schedule"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        games = soup.select('.ScheduleTables table tbody tr')
        teams = set()
        today = datetime.now().strftime('%a, %b %d')
        for game in games:
            date_header = game.find_previous('tr', class_='Table__TR Table__TR--sm Table__even')
            if date_header and today in date_header.text:
                cols = game.select('.Table__TD')
                if len(cols) >= 2:
                    teams.add(cols[0].text.strip())
                    teams.add(cols[1].text.strip())
        if not teams:
            raise Exception("No games found for today")
        return list(teams)
    except:
        return get_rotowire_slate()

def get_rotowire_slate():
    print("Scraping Rotowire for today's slate...")
    try:
        url = "https://www.rotowire.com/basketball/nba-lineups.php"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        teams = set()
        for matchup in soup.select('.lineup__abbr'):
            teams.add(matchup.text.strip())
        if not teams:
            raise Exception("No games found")
        return list(teams)
    except:
        return manual_slate_selection()

def manual_slate_selection():
    teams = ['ATL', 'BOS', 'BRK', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
             'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK',
             'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS']
    print("\nSlate Scrape Failed. Select teams manually:")
    for idx, team in enumerate(teams, 1):
        print(f"{idx}. {team}")
    selected = input("\nEnter team numbers (comma-separated): ").split(",")
    return [teams[int(i.strip()) - 1] for i in selected if i.strip().isdigit()]

# === CSV Loader ===
def load_csv_players():
    sources = [
        {'file': 'nba_roster_23_24_reg.csv', 'season': '23-24', 'type': 'Roster-Reg'},
        {'file': 'nba_roster_24_25_reg.csv', 'season': '24-25', 'type': 'Roster-Reg'},
        {'file': 'nba_playerstats_23_24_reg.csv', 'season': '23-24', 'type': 'Stats-Reg'}
    ]
    data = []
    for src in sources:
        with open(CSV_PATH + src['file'], mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                entry = {'source': 'CSV', 'season': src['season'], 'type': src['type']}
                entry.update(row)
                data.append(entry)
    return data

# === Fantasy Points Calculator ===
def calculate_fp(player):
    try:
        points = float(player.get('PTS', 0))
        rebounds = float(player.get('TRB', 0))
        assists = float(player.get('AST', 0))
        steals = float(player.get('STL', 0))
        blocks = float(player.get('BLK', 0))
        turnovers = float(player.get('TOV', 0))
        made_3pt = float(player.get('3P', 0))
        trip_dbl = int(player.get('Trp-Dbl', 0))
        fp = (
            points + rebounds * 1.25 + assists * 1.5 +
            steals * 2 + blocks * 2 + made_3pt * 0.5 +
            turnovers * -0.5 +
            (3 if trip_dbl >= 1 else 0) +
            (1.5 if sum([rebounds >= 10, assists >= 10, points >= 10, steals >= 10, blocks >= 10]) >= 2 else 0)
        )
        return round(fp, 2)
    except:
        return 0

# === DraftKings Lineup Optimizer ===
def generate_dk_lineup(players, salary_cap):
    lineup = []
    used_players = set()
    slots = [
        ('PG', ['PG']), ('SG', ['SG']), ('SF', ['SF']), ('PF', ['PF']),
        ('C', ['C']), ('G', ['PG', 'SG']), ('F', ['SF', 'PF']), ('UTIL', ['PG', 'SG', 'SF', 'PF', 'C'])
    ]
    for slot, eligible_positions in slots:
        candidates = [p for p in players if p['Player'] not in used_players and any(pos in p.get('Pos', '') for pos in eligible_positions)]
        candidates = sorted(candidates, key=lambda x: (x['FP'] / x['Salary']) if x['Salary'] > 0 else 0, reverse=True)
        for player in candidates:
            projected_total_salary = sum(p['Salary'] for p in lineup) + player['Salary']
            if projected_total_salary <= salary_cap:
                lineup.append({'Slot': slot, **player})
                used_players.add(player['Player'])
                break
    return lineup

# === Salary Adjustments ===
def adjust_lineup(lineup, players):
    print("\nLineup Adjustment Menu:")
    while True:
        for idx, player in enumerate(lineup, 1):
            print(f"{idx}. {player['Slot']} - {player['Player']} ({player['Team']}) - Pos: {player['Pos']} - Salary: {player['Salary']} - FP: {player['FP']}")
        choice = input("\nAdjust any salaries? (y/n): ").lower()
        if choice != 'y':
            break
        idx = int(input("Select player number: ")) - 1
        new_salary = input(f"Enter salary for {lineup[idx]['Player']} (current {lineup[idx]['Salary']}): ")
        if new_salary.isdigit():
            lineup[idx]['Salary'] = int(new_salary)
            for p in players:
                if p['Player'] == lineup[idx]['Player']:
                    p['Salary'] = int(new_salary)

# === Save Salaries ===
def save_salaries(players):
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f"{SALARY_LOG_PATH}{today}_salaries.json"
    salaries_log = [{'Player': p['Player'], 'Team': p.get('Team', ''), 'Pos': p.get('Pos', ''), 'Salary': p['Salary']} for p in players]
    with open(log_file, 'w') as file:
        json.dump(salaries_log, file, indent=4)
    print(f"\nSalaries saved: {log_file}")

# === Reflexive Loop ===
def reflexive_loop():
    while True:
        try:
            salary_cap = SALARY_CAP
            slate_teams = get_espn_slate()
            print(f"\nToday's Slate: {', '.join(slate_teams)}")
            manual_filter = input("\nWould you like to manually filter teams? (y/n): ").lower()
            if manual_filter == 'y':
                slate_teams = manual_slate_selection()

            players = load_csv_players()

            salary_logs = sorted([f for f in os.listdir(SALARY_LOG_PATH) if f.endswith('_salaries.json')], reverse=True)
            previous_salaries = dict()
            if salary_logs:
                with open(SALARY_LOG_PATH + salary_logs[0], 'r') as file:
                    prev_data = json.load(file)
                    previous_salaries = {p['Player']: {'Salary': p['Salary']} for p in prev_data}

            for p in players:
                if p['Player'] in previous_salaries:
                    p['Salary'] = previous_salaries[p['Player']]['Salary']
                else:
                    p['Salary'] = random.randint(3000, 10000)
                p['FP'] = calculate_fp(p)

            players = [p for p in players if p.get('Team') in slate_teams and p.get('Player')]
            print(f"\nData pull successful. Entries: {len(players)}")

            lineup = generate_dk_lineup(players, salary_cap)

            print("\nDraftKings Style Lineup:")
            for idx, player in enumerate(lineup, 1):
                print(f"{idx}. {player['Slot']} - {player['Player']} ({player['Team']}) - Pos: {player['Pos']} - Salary: {player['Salary']} - FP: {player['FP']}")

            adjust_lineup(lineup, players)
            save_salaries(players)

            print("\nWaiting 15 minutes for next cycle...\n")
            time.sleep(900)
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(900)

if __name__ == "__main__":
    reflexive_loop()
