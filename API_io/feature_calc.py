# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 19:57:47 2015

@author: Me
"""

import numpy as np
import pandas as pd
import itertools

col_names = ['first_dragon', 'blue_dragons', 'red_dragons',
             'first_baron', 'blue_barons', 'red_barons',
             'first_tower', 'blue_towers', 'red_towers',
             'first_inhib', 'blue_inhibs', 'red_inhibs',
             'first_blood', 'gold_diff', 'blue_kills',
             'red_kills', 'blue_share', 'red_share', 'surrender', 'winner']
             
def calc_features_single_match(match_info, last_min = 10):
    """ Calculate all features for a single game, and returns a pandas DataFrame

    Argument:
    full_match_info: a list of JSON objects containing League of Legends game timelines
    last_min: The minute through which to calculate stuff
    """    
    assert np.size(match_info['timeline']['frames']) >= last_min, '%r MatchId is too short' % match_info['matchId']

    # assign factor of first tower, need to update Dragon and Blood to match tower
    monster_features = calc_elite_monster_features(match_info, last_min)
    building_features = calc_building_features(match_info, last_min)
    first_blood = int( match_info['teams'][0]['firstBlood'])
    gold_diff = calc_gold_at_min(match_info, last_min)
    
    kills_features = assign_kills(match_info, last_min)
    surrendered = calc_surrender_feature(match_info)
    winner =  int(match_info['teams'][0]['winner'])
    
    # use itertools to make a single list
    all_features = list(itertools.chain.from_iterable([monster_features, building_features, [first_blood], 
                                        [gold_diff], kills_features, [surrendered], [winner]])) 
    return all_features
    
def calc_features_all_matches(full_match_info, last_min):
    """
    Apply calc_features_single_match to JSON of matches
    col_names defined at start of file
    """
    
    games_df = pd.DataFrame(index = np.arange(np.size(full_match_info)), columns= col_names)
    for i, cur_match in enumerate(full_match_info):
        games_df.loc[i] = calc_features_single_match(cur_match, last_min)
    
    games_df = retype_columns(games_df)    
    
    return games_df

def retype_columns(games_df):
    """ col_names defined at start of file """
    import re
    
    first_cols = [ col for col in col_names if re.search('^first', col) ]
    for col in first_cols:
        games_df[col] = games_df[col].astype('category')
    
    red_cols = [ col for col in col_names if re.search('^red.*s$', col) ]
    for col in red_cols:
        games_df[col] = games_df[col].astype(int)
        
    blue_cols = [ col for col in col_names if re.search('^blue.*s$', col) ]
    for col in blue_cols:
        games_df[col] = games_df[col].astype(int)
    
    games_df['gold_diff'] = games_df['gold_diff'].astype(int)
    
    share_cols = [ col for col in col_names if re.search('share$', col) ]
    for col in share_cols:
        games_df[col] = games_df[col].astype(float)
        
    games_df['surrender'] = games_df['surrender'].astype('category')
    games_df['winner'] = games_df['winner'].astype('category')
    return games_df
    
def factor_first_event(match_info, event_list, team_key):    
    """ Creates factor for an event in event_list
    
    Arguments:
    event_list: list of 'Event' objects
    team_key: string of the event type in the 'Team' object, e.g. 'firstTower'
    
    Returns:
    -1 if no event did not happen yet
    0 if red team did event
    1 if blue team did event
    """
    
    if event_list.size > 0:
        first_event_team = match_info['teams'][0][team_key]
        return int(first_event_team)
    else:
        return -1
            
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
        
    events_list = np.empty(0) # start with empty list
    for i in np.arange(1, last_min):
        cur_frame = np.array(match_info['timeline']['frames'][i]['events'])
        kill_indices = [x['eventType'] == event_name for x in cur_frame]
        events_list = np.append(events_list, cur_frame[np.array(kill_indices)])
    return events_list
    
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

def assign_kills( match_info, last_min = 10):
    """
    Assigns a kills to team100 or team200, then sums all tlhe kills
    
    Arguments: 
    see identify_kills
    
    Returns:
    Number of kills for each team, and carry's share of kills
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
    
def calc_building_features(match_info, last_min = 10):
    """ Calculates which team killed first tower, as well as number of tower kills for each team
    """
    
    building_deaths = identify_events(match_info, 'BUILDING_KILL', last_min)
    
    if building_deaths.size >0:
        # separate out the tower deaths and building_deaths
        tower_deaths = building_deaths[np.array([x['buildingType'] == 'TOWER_BUILDING' for x in building_deaths])]
        inhib_deaths = building_deaths[np.array([x['buildingType'] == 'INHIBITOR_BUILDING' for x in building_deaths])]
        
        # calculate factor for whether first building was killed, and which team got it
        first_tower_factor = factor_first_event(match_info, tower_deaths, 'firstTower')
        first_inhib_factor = factor_first_event(match_info, inhib_deaths, 'firstInhibitor')
        
        # sum up kills for each team
        blue_tower_kills = np.sum([x['teamId'] == 200 for x in tower_deaths])
        red_tower_kills = np.sum([x['teamId'] == 100 for x in tower_deaths])
        
        blue_inhib_kills = np.sum([x['teamId'] == 200 for x in inhib_deaths])
        red_inhib_kills = np.sum([x['teamId'] == 100 for x in inhib_deaths])
        
        return [first_tower_factor, blue_tower_kills, red_tower_kills, first_inhib_factor, blue_inhib_kills, red_inhib_kills]
    else:
        return [-1, 0, 0, -1, 0, 0]
        
def calc_elite_monster_features(match_info, last_min = 10):
    """ Calculates which team got first dragon, and number of dragons per team """
    monster_events = identify_events(match_info, 'ELITE_MONSTER_KILL', last_min)
     
    if monster_events.size > 0:
        # separate out the tower deaths and building_deaths
        drag_deaths = monster_events[np.array([x['monsterType'] == 'DRAGON' for x in monster_events])]
        baron_deaths = monster_events[np.array([x['monsterType'] == 'BARON_NASHOR' for x in monster_events])]
        
        # calculate factor for whether first building was killed, and which team got it
        first_drag_factor = factor_first_event(match_info, drag_deaths, 'firstDragon')
        first_baron_factor = factor_first_event(match_info, baron_deaths, 'firstBaron')
        
        # sum up kills for each team
        blue_drag_kills = np.sum([x['killerId'] < 6 for x in drag_deaths])
        red_drag_kills = np.sum([x['killerId'] > 5 for x in drag_deaths])
        
        blue_baron_kills = np.sum([x['killerId'] < 6 for x in baron_deaths])
        red_baron_kills = np.sum([x['killerId'] > 5 for x in baron_deaths])
        
        return [first_drag_factor, blue_drag_kills, red_drag_kills, first_baron_factor, blue_baron_kills, red_baron_kills]
    else:
        return [-1, 0, 0, -1, 0, 0]
        
def calc_surrender_feature(match_info):
    """ Game is surrendered if <2 nexus turrets were destroyed
    """
    game_length = len(match_info['timeline']['frames'])
    building_deaths = identify_events(match_info, 'BUILDING_KILL', game_length-1)
    tower_deaths = building_deaths[np.array([x['buildingType'] == 'TOWER_BUILDING' for x in building_deaths])]
    nexus_tower_deaths = tower_deaths[np.array([x['towerType'] == 'NEXUS_TURRET' for x in tower_deaths])]
    
    return int( nexus_tower_deaths.size < 2)
