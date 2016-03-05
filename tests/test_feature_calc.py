# -*- coding: utf-8 -*-
"""
to run, execute: nosetests test_feature_calc.py

Created on Wed Feb 24, 2016

@author: Michael Patterson, map222@gmail.com
"""

import json
import pandas as pd
from nose.tools import assert_equals, assert_almost_equals
import lolML.src.feature_calc as feature_calc

working_dir = 'C:\\Users\\Chauncey\\Documents\\GitHub\\LolML\\tests\\'

# load in json data
with open(working_dir + 'ten match info.json', 'r') as json_file:
    ten_match_info = json.load( json_file)
one_match_info = ten_match_info[0]

timepoint = 15

# load in pandas dataframe of correctly feature calced data (at minute 15)
ten_match_df = pd.read_csv('ten match df.csv', sep=';', index_col='matchId')

def test_calc_building_features():
    values_buildings = feature_calc.calc_building_features(one_match_info, timepoint)
    building_col = ['first_tower', 'tower_diff', 'total_tower', 'first_inhib', 'blue_inhibs', 'red_inhibs']
    df_buildings = ten_match_df[building_col].iloc[0].values
    assert_equals( values_buildings, list(df_buildings)) # convert from numpy array to list
    
def test_calc_elite_monster_features():
    values_monsters = feature_calc.calc_elite_monster_features(one_match_info, timepoint)
    monster_col = ['first_dragon', 'drag_diff', 'total_drag', 'first_baron', 'blue_barons', 'red_barons']
    df_monsters = ten_match_df[monster_col].iloc[0].values
    assert_equals( values_monsters, list(df_monsters)) # convert from numpy array to list
    
def test_calc_surrender_feature():
    values_surrender= [feature_calc.calc_surrender_feature(x) for x in ten_match_info]
    assert_equals(values_surrender, list(ten_match_df['surrender'].values))

def test_gold_calc():
    values_gold = [feature_calc.calc_gold_at_min(x, timepoint) for x in ten_match_info]
    assert_equals(values_gold, list(ten_match_df['gold_diff'].values))

def test_assign_kills(): # could be nice to map this over all matches
    values_kills = feature_calc.assign_kills(ten_match_info[0], timepoint)
    kill_col = ['kill_diff', 'total_kill', 'blue_share', 'red_share']
    df_kills = ten_match_df[kill_col].iloc[0].values
    assert_almost_equals( list(values_kills), list(df_kills))

def test_parse_team_comp():
    values_team_comps = feature_calc.parse_team_comp(ten_match_info[0])
    values_team_comps = [item for sublist in values_team_comps for item in sublist]
    team_col = ['blue_0', 'blue_1', 'blue_2', 'blue_3', 'blue_4',
             'red_0', 'red_1', 'red_2', 'red_3', 'red_4',]
    df_team_comp = ten_match_df[team_col].iloc[0].values
    assert_equals(values_team_comps, list(df_team_comp))

def test_calc_secondary_features():
    secondary_col = ['square_gold_diff']
    values_2ndary_features = feature_calc.calc_secondary_features( ten_match_df )[secondary_col].values
    df_2ndary = ten_match_df[secondary_col].values
    assert_equals(list(values_2ndary_features), list(df_2ndary))
    
#def test_calc_features_all_matches(): does not work for now
#    non_float_col = [x for x in ten_match_df.columns if x not in ['blue_share', 'red_share'] ]
#    calc_df = feature_calc.calc_features_all_matches(ten_match_info, timepoint)
#    assert calc_df['non_float_col'].equals( ten_match_df['non_float_col']) 