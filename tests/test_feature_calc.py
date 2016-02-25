# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24, 2016

@author: Michael Patterson, map222@gmail.com
"""

import json
import pandas as pd
from nose.tools import assert_equals
import lolML.src.feature_calc as feature_calc

working_dir = 'C:\\Users\\Chauncey\\Documents\\GitHub\\LolML\\tests\\'

# load in json data
with open(working_dir + 'ten match info.json', 'r') as json_file:
    ten_match_info = json.load( json_file)
one_match_info = ten_match_info[0]

timepoint = 15

# load in pandas dataframe of correctly feature calced data
ten_match_df = pd.read_csv('ten match df.csv', sep=';', index_col='matchId')

def test_calc_building_features():
    calc_buildings = feature_calc.calc_building_features(one_match_info, timepoint)
    building_col = ['first_tower', 'tower_diff', 'total_tower', 'first_inhib', 'blue_inhibs', 'red_inhibs']
    df_buildings = ten_match_df[building_col].iloc[0].values
    assert_equals( calc_buildings, list(df_buildings)) # convert from numpy array to list
    
def test_calc_elite_monster_features():
    calc_monsters = feature_calc.calc_elite_monster_features(one_match_info, timepoint)
    monster_col = ['first_dragon', 'drag_diff', 'total_drag', 'first_baron', 'blue_barons', 'red_barons']
    df_monsters = ten_match_df[monster_col].iloc[0].values
    assert_equals( calc_monsters, list(df_monsters)) # convert from numpy array to list
    
def test_calc_surrender_feature():
    calc_surrender = feature_calc.calc_surrender_feature(one_match_info)
    assert_equals(calc_surrender, ten_match_df['surrender'].iloc[0])
    
def test_no_calc_surrender_feature():
    calc_surrender = feature_calc.calc_surrender_feature(ten_match_info[2])
    assert_equals(calc_surrender, ten_match_df['surrender'].iloc[2])
    
#def test_calc_features_all_matches(): does not work for now
#    non_float_col = [x for x in ten_match_df.columns if x not in ['blue_share', 'red_share'] ]
#    calc_df = feature_calc.calc_features_all_matches(ten_match_info, timepoint)
#    assert calc_df['non_float_col'].equals( ten_match_df['non_float_col']) 