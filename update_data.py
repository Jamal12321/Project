import time
import requests
import json
import ssl
from env import PARSING_KEY


ssl._create_default_https_context = ssl._create_unverified_context

def make_request(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            return response
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"  Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
    return None
TEAM_IDS = {}
LEAGUES_DATA = {}
need_leagues = ['PL', 'BL1', 'FL1', 'SA', 'PD']
headers = {'X-Auth-Token': PARSING_KEY}


url = "https://api.football-data.org/v4/competitions/"

try:
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("Таймаут при подключении к API")
    exit()
except requests.exceptions.RequestException as e:
    print(f"Ошибка подключения: {e}")
    exit()

data = response.json()

for league in data['competitions']:
    league_code = league['code']
    
    if league_code in need_leagues:
        url_teams = f"https://api.football-data.org/v4/competitions/{league_code}/teams"
        
        try:
            response_teams = requests.get(url_teams, headers=headers, timeout=30, verify=False)
            response_teams.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"Таймаут для лиги {league_code}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Ошибка для лиги {league_code}: {e}")
            continue
        
        data_teams = response_teams.json()
        
        if 'teams' not in data_teams:
            print(f"У лиги {league_code} нет ключа 'teams'")
            continue
        
        team_list = []
        for team in data_teams['teams']:
            team_list.append(team['name'])
            TEAM_IDS[team['name']] = team['id']
        
        LEAGUES_DATA[league_code] = {
            'name': league['name'],
            'country': league['area']['name'],
            'teams': team_list
        }
        print(f"Загружена лига: {league_code} ({len(team_list)} команд)")

TEAMS_FORM = {}
total_teams = sum(len(data['teams']) for data in LEAGUES_DATA.values())
current = 0

for league, data in LEAGUES_DATA.items():
    teams = data['teams']
    for team in teams:
        current += 1
        team_id = TEAM_IDS.get(team)
        if not team_id:
            print(f"Нет ID для команды {team}")
            continue
        
        print(f"[{current}/{total_teams}] Обработка: {team}")
        
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches?limit=5&status=FINISHED"
        
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            print(f"  Таймаут для {team}, пропускаем")
            continue
        except requests.exceptions.RequestException as e:
            print(f"  Ошибка для {team}: {e}")
            continue
        
        match_data = response.json()
        
        if 'matches' not in match_data:
            print(f"  У команды {team} нет ключа 'matches'")
            continue
        
        wins = 0
        draws = 0
        losses = 0
        
        for match in match_data['matches']:
            winner = match['score']['winner']
            
            if winner == 'DRAW':
                draws += 1
            elif winner == 'HOME_TEAM' and team_id == match['homeTeam']['id']:
                wins += 1
            elif winner == 'AWAY_TEAM' and team_id == match['awayTeam']['id']:
                wins += 1
            else:
                losses += 1
        
        TEAMS_FORM[team] = {
            'wins': wins,
            'draws': draws,
            'losses': losses
        }
        
        time.sleep(3) 
with open('leagues_data.json', 'w', encoding='utf-8') as f:
    json.dump(LEAGUES_DATA, f, ensure_ascii=False, indent=2)

with open('teams_form.json', 'w', encoding='utf-8') as f:
    json.dump(TEAMS_FORM, f, ensure_ascii=False, indent=2)

with open('last_update.txt', 'w') as f:
    f.write(str(time.time()))

print(f"\nДанные успешно сохранены в файлы!")
print(f"   - Лиг: {len(LEAGUES_DATA)}")
print(f"   - Команд: {len(TEAMS_FORM)}")