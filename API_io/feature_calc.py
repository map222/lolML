# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 19:57:47 2015

@author: Me
"""

import numpy as np
import pandas as pd

def calc_gold_at_min( match_info, last_min ):
    """
    Calculate the gold for each team at 10 minutes (10th frame), and return the difference
    
    Argument:
    match_info: a JSON of a single match
    
    Returns:
    The difference between the sum of team100's gold and team200's gold (I think team100 = blue)
    """
    
    tenmin_frame = match_info['timeline']['frames'][last_min]['participantFrames'] # plus one because 0 = time 0
    team100_gold = [tenmin_frame[x]['totalGold'] for x in ['1', '2', '3', '4', '5'] ]
    team200_gold = [tenmin_frame[x]['totalGold'] for x in ['6', '7', '8', '9', '10'] ]
    
    return sum(team100_gold) - sum(team200_gold)
    
def identify_events( match_info, event_name, last_min =10):
    """
    Get dictionary of events from a match; see assign_kills for example call of function
    
    Arguments:
    match_info: a JSON of a single match
    event_name: name of event you are looking for; this is key for dictionary
    last_min: integer of last minute to look at
    
    Returns:
    A numpy array containing events for champion kills
    """
    
    champion_kills = np.empty(0) # start with empty list
    for i in np.arange(1, last_min):
        cur_frame = np.array(match_info['timeline']['frames'][i]['events'])
        kill_indices = [x['eventType'] == event_name for x in cur_frame]
        champion_kills = np.append(champion_kills, cur_frame[np.array(kill_indices)])
    return champion_kills
    
def assign_kills( match_info, last_min = 10):
    """
    Assigns a kills to team100 or team200, then sums all tlhe kills
    
    Arguments: 
    see identify_kills
    
    Returns:
    Two integers, with explanatory names
    """    
    
    champion_kills = identify_events(match_info, 'CHAMPION_KILL', last_min) # get the kill events from JSON
    killers = np.array([x['killerId'] for x in champion_kills]) # identify killers
    
    # sum kills for each team
    team100_kills = sum(killers < 6) # blue team is ID's 1-5
    team200_kills = sum(killers > 5)
    
    # calculate share of team kills for person with most
    kill_counts, _ = np.histogram(killers)
    team100_share = kill_counts[:5].max()
    team200_share = kill_counts[5:].max()
    
    return team100_kills, team200_kills, team100_share / max(team100_kills, 1), team200_share / max(team200_kills, 1)
    
def calc_features_single_match(match_info, last_min = 10):
    """ Calculate all features for a single game, and returns a pandas DataFrame

    Argument:
    full_match_info: a list of JSON objects containing League of Legends game timelines
    last_min: The minute through which to calculate stuff
    """    

    # assign factor of first tower, need to update Dragon and Blood to match tower
    first_dragon = match_info['teams'][0]['firstDragon']
    first_tower = calc_first_tower(match_info, last_min)
    first_blood = match_info['teams'][0]['firstBlood']
    gold_diff = calc_gold_at_min(match_info, last_min)
    
    blue_kills, red_kills, blue_share, red_share = assign_kills(match_info, last_min)
    winner =  match_info['teams'][0]['winner']
    col_names = ['first_dragon', 'first_tower', 'first_blood', 'gold_diff', 'blue_kills',
                 'red_kills', 'blue_share', 'red_share', 'winner']
    
    return [first_dragon, first_tower, first_blood, gold_diff, blue_kills, red_kills, blue_share, red_share, winner]
    
def calc_features_all_matches(full_match_info, last_min):
    """
    Apply calc_features_single_match to JSON of matches
    """
    col_names = ['first_dragon', 'first_tower', 'first_blood', 'gold_diff', 'blue_kills',
                 'red_kills', 'blue_share', 'red_share', 'winner']
    games_df = pd.DataFrame(index = np.arange(np.size(full_match_info)), columns= col_names)
    for i, cur_match in enumerate(full_match_info):
        games_df.loc[i] = calc_features_single_match(cur_match, last_min)
    
    games_df = retype_columns(games_df)    
    
    return games_df

def retype_columns(games_df):
    
    col_names = ['first_dragon', 'first_tower', 'first_blood', 'gold_diff', 'blue_kills',
                 'red_kills', 'blue_share', 'red_share', 'winner']
    for x in col_names[:3]:
        games_df[x] = games_df[x].astype(int).astype('category')
    games_df[col_names[3:6]] = games_df[col_names[3:6]].astype(int)
    games_df[col_names[6:8]] = games_df[col_names[6:8]].astype(float)
    games_df[col_names[-1]] = games_df[col_names[-1]].astype(int).astype('category')
    return games_df

def calc_first_tower(match_info, last_min = 10):
    """ Calculates whether first tower fell within timeframe
    
    Returns:
    -1 if no tower fallen yet
    0 if red team killed tower
    1 if blue team killed tower
    """
    
    tower_deaths = identify_events(match_info, 'BUILDING_KILL', last_min)
    tower_flag =  tower_deaths.size > 1
    
    first_tower_team = match_info['teams'][0]['firstTower']
    if tower_flag:
        return np.array(first_tower_team).astype(int)
    else:
        return np.array(-1)