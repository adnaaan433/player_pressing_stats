import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

def get_competitions(username='Jack71299@hotmail.co.uk', 
                     password='J7rB7aP2'):
    url = "https://data.statsbombservices.com/api/v4/competitions"
    
    if username and password:
        response = requests.get(url, auth=(username, password))
    else:
        response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None
    
    cdf = pd.DataFrame(response.json())
    cdf = cdf[cdf['competition_name'].isin(['1. Bundesliga', 'La Liga', 'Premier League', 'Serie A', 'Ligue 1'])]
    cdf = cdf[['competition_id', 'season_id', 'country_name', 'competition_name', 'season_name']].reset_index(drop=True)
    
    return cdf

def get_matches_id(competition_id, season_id,
                   username='Jack71299@hotmail.co.uk', 
                   password='J7rB7aP2'):
    url = f"https://data.statsbombservices.com/api/v6/competitions/{competition_id}/seasons/{season_id}/matches"

    if username and password:
        response = requests.get(url, auth=(username, password))
    else:
        response = requests.get(url)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None
    
    mdf = pd.DataFrame(response.json())
    mdf = mdf[['home_team', 'away_team']]
    # We use .apply(pd.Series) to expand the dictionary keys into columns
    home_split = mdf['home_team'].apply(pd.Series)
    away_split = mdf['away_team'].apply(pd.Series)

    # Concatenate the new columns back to the original dataframe
    # axis=1 means we are adding columns, not rows
    mdf = pd.concat([mdf, home_split, away_split], axis=1)

    # Drop the original combined columns
    mdf = mdf.drop(columns=['home_team', 'away_team'])
    mdf = mdf[['home_team_name', 'away_team_name']]
    
    return mdf

def find_competition_season(competition_name, season_name, username='Jack71299@hotmail.co.uk', 
                           password='J7rB7aP2'):
    cdf = get_competitions(username, password)
    
    if cdf is None:
        return None, None
    
    matches = cdf[
        (cdf['competition_name'].str.contains(competition_name, case=False, na=False)) &
        (cdf['season_name'].str.contains(season_name, case=False, na=False))
    ]
    
    if len(matches) == 0:
        print(f"\nNo matches found for competition '{competition_name}' and season '{season_name}'")
        print("\nAvailable competitions and seasons:")
        print(cdf[['competition_name', 'season_name']].drop_duplicates().to_string(index=False))
        return None, None
    
    if len(matches) > 1:
        print(f"\nMultiple matches found for '{competition_name}' and '{season_name}':")
        print(matches[['competition_name', 'season_name', 'competition_id', 'season_id']])
        print("\nUsing the first match.")
    
    competition_id = str(matches.iloc[0]['competition_id'])
    season_id = str(matches.iloc[0]['season_id'])
    
    print(f"\nFound: {matches.iloc[0]['competition_name']} - {matches.iloc[0]['season_name']}")
    print(f"Competition ID: {competition_id}, Season ID: {season_id}")
    
    return competition_id, season_id

def get_player_stats(season_id, competition_id, 
                     username='Jack71299@hotmail.co.uk', 
                     password='J7rB7aP2'):
    url = f"https://data.statsbombservices.com/api/v4/competitions/{competition_id}/seasons/{season_id}/player-stats"
    
    if username and password:
        response = requests.get(url, auth=(username, password))
    else:
        response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None
    
    pdf = pd.DataFrame(response.json())
    
    return pdf

def get_short_name(full_name):
    if pd.isna(full_name):
        return full_name
    parts = full_name.split()
    if len(parts) == 1:
        return full_name
    elif len(parts) == 2:
        return parts[0][0] + ". " + parts[1]
    else:
        return parts[0][0] + ". " + parts[1][0] + ". " + " ".join(parts[2:])

def get_players_df(competition_name, season_name, team_name, 
                   username='Jack71299@hotmail.co.uk', 
                   password='J7rB7aP2'):
    competition_id, season_id = find_competition_season(
        competition_name, season_name, username, password
    )
    
    if competition_id is None or season_id is None:
        return None
    
    pdf = get_player_stats(season_id, competition_id, username, password)
    
    if pdf is None:
        return None
    
    pdf.columns = pdf.columns.str.replace('player_season_', '', regex=False)
    
    pdf = pdf[['player_name', 'player_known_name', 'team_name',
            'minutes', '90s_played', 'pressures_90', 'counterpressures_90']]
    
    team_matches = pdf[pdf['team_name'].str.contains(team_name, case=False, na=False)]
    
    if len(team_matches) == 0:
        print(f"\nTeam '{team_name}' not found.")
        print("\nAvailable teams:")
        print(sorted(pdf['team_name'].unique()))
        return None
    
    pdf = team_matches
    pdf['player_known_name'] = pdf['player_known_name'].fillna(pdf['player_name'])
    
    pdf['pressures'] = pdf['pressures_90'] * pdf['90s_played']
    pdf['counterpressures'] = pdf['counterpressures_90'] * pdf['90s_played']
    pdf['total'] = pdf['pressures'] + pdf['counterpressures']
    pdf['team_percentage'] = pdf['total'] / pdf['total'].sum() * 100
    pdf['short_name'] = pdf['player_known_name'].apply(get_short_name)
    pdf = pdf.sort_values(by='total', ascending=False).reset_index(drop=True)

    return pdf

def plot_top10_pressers(competition_name, season_name, team_name,
                       username='Jack71299@hotmail.co.uk', 
                       password='J7rB7aP2'):
    pdf = get_players_df(competition_name, season_name, team_name, username, password)
    
    if pdf is None:
        return
    
    top10 = pdf.head(10).copy()

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_facecolor('#1a1a1a')

    pressure_color = '#00d9ff'
    counterpressure_color = '#ff6b35'

    y_pos = np.arange(len(top10))
    bar_height = 0.6

    bars1 = ax.barh(y_pos, top10['pressures'], bar_height, 
                    label='Pressures', color=pressure_color, alpha=0.85)
    bars2 = ax.barh(y_pos, top10['counterpressures'], bar_height, 
                    left=top10['pressures'], label='Counter Pressures', 
                    color=counterpressure_color, alpha=0.85)

    for i, (idx, row) in enumerate(top10.iterrows()):
        pressure_x = row['pressures'] / 2
        if row['pressures'] > 0:
            ax.text(pressure_x, i, f"{int(row['pressures'])}", 
                    ha='center', va='center', fontsize=10, fontweight='bold', 
                    color='white')
        
        counter_x = row['pressures'] + (row['counterpressures'] / 2)
        if row['counterpressures'] > 0:
            ax.text(counter_x, i, f"{int(row['counterpressures'])}", 
                    ha='center', va='center', fontsize=10, fontweight='bold', 
                    color='white')

    # Add total and percentage text at the end of each bar
    for i, (idx, row) in enumerate(top10.iterrows()):
        bar_end = row['total']
        percentage = row['team_percentage']
        total = int(row['total'])
        
        # Add total and percentage text at the end of bar
        ax.text(bar_end + 5, i, f"{total} ({percentage:.1f}%)", 
                ha='left', va='center', fontsize=11, 
                fontweight='bold', color='#ffd700')

    # Customize axes
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top10['short_name'], fontsize=11, fontweight='bold')
    ax.set_xlabel('Total Pressures', fontsize=12, 
                fontweight='bold', color='white')
    ax.set_title(f"{team_name} Top 10 Pressers", 
                fontsize=25, fontweight='bold', pad=50, color='white')
    ax.text(0.5, 1.05, f'{competition_name} - {season_name} | Data: Statsbomb | made by: @adnaaan433', 
            fontsize=12, color='white', ha='center', transform=ax.transAxes)

    # Grid
    ax.grid(axis='x', alpha=0.2, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    ax.invert_yaxis()
    ax.set_xlim(0, top10['total'].max() + 50)

    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#444444')
    ax.spines['bottom'].set_color('#444444')

    # Legend
    legend_elements = [
        mpatches.Patch(color=pressure_color, label='Pressures', alpha=0.85),
        mpatches.Patch(color=counterpressure_color, label='Counter Pressures', alpha=0.85),
        mpatches.Patch(color='#ffd700', label='Total (Team %)', alpha=0.85)
    ]
    ax.legend(handles=legend_elements, loc='lower right', framealpha=0.9,
            facecolor='#2a2a2a', edgecolor='#444444', fontsize=10)
    
    return fig, pdf