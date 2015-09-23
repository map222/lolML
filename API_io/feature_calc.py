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
    team100_kills = sum([x['killerId'] < 6 for x in champion_kills]) # blue team is ID's 1-5
    team200_kills = sum([x['killerId'] > 5 for x in champion_kills]) 
    
    return team100_kills, team200_kills
    
def calc_all_features(full_match_info, last_min = 10):
    """ Calculate all features for a game, and returns a pandas DataFrame

    Argument:
    full_match_info: a list of JSON objects containing League of Legends game timelines
    last_min: The minute through which to calculate stuff
    """    
    
    games_df = pd.DataFrame()
    # only look at first team, since results are symmetric
    games_df['first_dragon'] = [ x['teams'][0]['firstDragon'] for x in full_match_info ]
    
    # assign first tower if it exists
    valid_towers = [validate_first_tower(x, last_min) for x in full_match_info]
    first_tower_team = [ x['teams'][0]['firstTower'] for x in full_match_info ]
    def assign_maybe_event(valid, team):
        if valid:
            return team
        else:
            return None
    games_df['first_tower'] = [ assign_maybe_event(x[0], x[1]) for x in zip(valid_towers, first_tower_team)] 
    games_df['first_blood'] = [ x['teams'][0]['firstBlood'] for x in full_match_info ]
    games_df['gold_diff'] = [ calc_gold_at_min(x, last_min) for x in full_match_info]
    
    games_df['blue_kills'] = 0 # need to initialize these columns, so you can assign as tuple later
    games_df['red_kills'] = 0
    games_df[['blue_kills', 'red_kills']] = [ assign_kills(x, last_min) for x in full_match_info]
    games_df['winner'] = [ x['teams'][0]['winner'] for x in full_match_info ]
    
    return games_df

def validate_first_tower(match_info, last_min = 10):
    """ Calculates whether first tower fell within timeframe
    """
    tower_deaths = identify_events(match_info, 'BUILDING_KILL', last_min)
    return tower_deaths.size > 1