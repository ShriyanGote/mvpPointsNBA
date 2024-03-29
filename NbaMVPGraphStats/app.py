from flask import Flask, render_template, request
from flask import redirect, url_for
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib as mpl
import math
import requests
import matplotlib.pyplot as plt

app = Flask(__name__)

# Existing functions (extract_team_info, bubble_sort, etc.) -----------------------------------------------------------------------------
def get_mvp_data(data,player):
    return np.asarray(data[data['Player'] == player])[0]

# Function to calculate the MVP score
def calculate_score(player_stats):
    efg = player_stats[3] * 60
    stl = player_stats[4] * 20
    rbs = player_stats[5] * 3
    ast = player_stats[6] * 4
    pts = player_stats[7] * 1
    wins = player_stats[14]
    rank = player_stats[15]
    score = (0.15 * (wins + rank)) + (0.28 * pts) + (0.12 * rbs) + (0.16 * ast) + (0.21 * efg) + (0.08 * stl)
    return round(score, 2)

def extract_team_info(row):
    team_name = row.find('a').text
    team_abbr = row.find('a')['href'].split('/')[-2].upper()
    wins = int(row.find('td', {'data-stat': 'wins'}).text)
    losses = int(row.find('td', {'data-stat': 'losses'}).text)
    win_loss_pct = row.find('td', {'data-stat': 'win_loss_pct'}).text

    return {
        'Team Name': team_name,
        'Team Abbreviation': team_abbr,
        'Wins': wins,
        'Losses': losses,
        'Win-Loss Percentage': win_loss_pct
    }

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        # Last i elements are already sorted, so we don't need to check them
        for j in range(0, n-i-1):
            if arr[j]['Wins'] > arr[j+1]['Wins']:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr


#enter all teams 
def get_team(all_teams, team_abb):
    for i in all_teams:
        if i['Team Abbreviation'] == team_abb:
            return i
        if i['Team Abbreviation'] == 'TOT':
            return -1
# ... (other existing functions) ---------------------------------------------------


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        team_year_stats = request.form['year']
        return redirect(url_for('result', year=team_year_stats))

    return render_template('index.html')


@app.route('/result', methods=['GET', 'POST'])


def result():
    
    team_year_stats = request.args.get('year')
    lwr_points = request.args.get('lwr_points')
    if not lwr_points:
        lwr_points = 15
    else:
        lwr_points = int(lwr_points)
    lwr_efg = request.args.get('lwr_efg')
    if not lwr_efg:
        lwr_efg = 40
    else:
        lwr_efg = int(lwr_efg)
    lwr_gs = request.args.get('lwr_gs')
    if not lwr_gs:
        lwr_gs = 40
    else:
        lwr_gs = int(lwr_gs)

    if not team_year_stats:
        return redirect(url_for('index'))
    url_team = "https://www.basketball-reference.com/leagues/NBA_"+team_year_stats+"_standings.html"
    response = requests.get(url_team)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        team_row = soup.find('tr')
        eastern_table = soup.find('table', {'id': 'divs_standings_E'})
        western_table = soup.find('table', {'id': 'divs_standings_W'})

        
        eastern_teams = [extract_team_info(row) for row in eastern_table.find_all('tr', {'class': 'full_table'})]
        western_teams = [extract_team_info(row) for row in western_table.find_all('tr', {'class': 'full_table'})]

        all_teams = bubble_sort(eastern_teams + western_teams)
        
        result_data = []
        for i in range(len(all_teams)):
            all_teams[i]['Rank'] = i + 1

        url_player = "https://www.basketball-reference.com/leagues/NBA_"+team_year_stats+"_per_game.html"
        html_player = urlopen(url_player)
        stats_Page = BeautifulSoup(html_player, features = "html.parser")
        column_Headers_player = stats_Page.findAll('tr')[0]
        column_Headers_player = [i.getText() for i in column_Headers_player.findAll("th")]

        rows_player = stats_Page.findAll('tr')[1:]
        player_Stats = []
        for i in range(len(rows_player)):
            player_Stats.append([col.getText() for col in rows_player[i].findAll("td")])

        data = pd.DataFrame(player_Stats, columns = column_Headers_player[1:])

        mvpCategories = ["GS", "eFG%","STL","TRB", "AST", "PTS"]
        mvpRadar_player = data[["Player", 'Tm'] + mvpCategories]
        mvpRadar_team = data[["Player", "Tm"]]


        for i in mvpCategories:
            mvpRadar_player.loc[:, i] = pd.to_numeric(data[i])

        mvpDataFiltered = mvpRadar_player[mvpRadar_player["PTS"] > lwr_points]
        mvpDataFiltered = mvpDataFiltered[mvpDataFiltered["GS"] > lwr_gs]
        mvpDataFiltered = mvpDataFiltered[mvpDataFiltered["eFG%"] > lwr_efg * 0.01]

        for i in mvpCategories:
            mvpDataFiltered[i + "_Rk"] = round(mvpDataFiltered[i].rank(pct = True), 3)


        for name in mvpDataFiltered['Player']:
            player = get_mvp_data(mvpDataFiltered, name)
            player_team = get_team(all_teams,str(player[1]))
            if player_team == None:
                result_data.append({
                    'Player': name + " (Multiple Teams -> Not Eligible)",
                    'MVP Score': 0.0
                })
                continue
            player_fullstats = np.hstack((player, [player_team['Wins'], player_team['Rank']]))
            result_data.append({
                'Player': name,
                'MVP Score': calculate_score(player_fullstats)
            })

        result_data_sorted = sorted(result_data, key=lambda x: x['MVP Score'], reverse=True)
        unique_players = set()
        unique_result_data = []

        for player_data in result_data_sorted:
            player_name = player_data['Player']
            if player_name not in unique_players:
                unique_players.add(player_name)
                unique_result_data.append(player_data)

        return render_template('result.html', result=unique_result_data)
        
    else:
        print(f'Failed to fetch the webpage. Status code: {response.status_code}')


if __name__ == '__main__':
    app.run(debug=True)