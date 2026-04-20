import os
import json
import time
import requests
from flask import Flask, render_template, jsonify, request
from bs4 import BeautifulSoup
from env import SECRET_KEY, PARSING_KEY
import random
os.system('pip install -r requirements.txt > nul 2>&1')
SECRET_KEY = os.getenv('SECRET_KEY')
PARSING_KEY = os.getenv('PARSING_KEY')
app = Flask(__name__)
app.secret_key = SECRET_KEY

LEAGUES_DATA = {}
TEAMS_FORM = {}
    

def load_data():
    global LEAGUES_DATA, TEAMS_FORM
    
    if os.path.exists('leagues_data.json') and os.path.exists('teams_form.json'):
        with open('leagues_data.json', 'r', encoding='utf-8') as f:
            LEAGUES_DATA = json.load(f)
        with open('teams_form.json', 'r', encoding='utf-8') as f:
            TEAMS_FORM = json.load(f)
        print("Данные загружены из файлов")
        return True
    else:
        print("Файлы с данными не найдены. Запустите update_data.py")
        return False
print("Ключи в LEAGUES_DATA:", list(LEAGUES_DATA.keys()))


if os.path.exists('last_update.txt'):
    with open('last_update.txt', 'r') as f:
        last_update = float(f.read())
    
    hours_passed = (time.time() - last_update) / 3600
    
    if hours_passed < 24:
        print(f"Данные свежие (обновлены {hours_passed:.1f} часов назад)")
    else:
        print("Данные устарели (более 24 часов), рекомендуется запустить update_data.py")
else:
    print("запустите update_data.py для загрузки данных")
load_data()
print("Количество команд в TEAMS_FORM:", len(TEAMS_FORM))
if len(TEAMS_FORM) > 0:
    print("Пример:", list(TEAMS_FORM.items())[:3])
else:
    print("TEAMS_FORM пуст! Запусти update_data.py")





def take_url():
    response = requests.get('https://www.flashscorekz.com/?rd=flashscore.ru')
    if response.status_code == 200:
        return response.text
    else:
        return None

@app.route('/')
def main():
    predictions = []
    return render_template('index.html', predictions=predictions)

@app.route('/get_teams')
def get_teams():
    league = request.args.get('league')
    if league in LEAGUES_DATA:
        return jsonify(LEAGUES_DATA[league]['teams'])
    else:
        return jsonify([])

@app.route('/predict')
def predict():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    

    form1 = TEAMS_FORM.get(team1, {'wins': 2, 'draws': 1, 'losses': 2})
    form2 = TEAMS_FORM.get(team2, {'wins': 2, 'draws': 1, 'losses': 2})

    power1 = (form1['wins'] * 2 + form1['draws'] * 1) / 5
    power2 = (form2['wins'] * 2 + form2['draws'] * 1) / 5

    home_power = power1 * 1.2
    away_power = power2 * 0.9
    
    total = home_power + away_power
    
    if total > 0:
        home_win = round(home_power / total, 2)
        away_win = round(away_power / total, 2)
        draw = round(1 - home_power - away_power, 2)
    else:
        home_win = 0.33
        draw = 0.34
        away_win = 0.33
    
    return jsonify({
        'team1': team1,
        'team2': team2,
        'home_win': home_win,
        'draw': draw,
        'away_win': away_win
    })

if __name__ == '__main__':
    app.run(debug=True)
