# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 19:57:47 2015

@author: Me
"""

def calc_gold_at10( match_info ):
    """
    Calculate the gold for each team at 10 minutes (10th frame), and return the difference
    
    Argument:
    match_info: a JSON of a single match
    
    Returns:
    The difference between the sum of team100's gold and team200's gold (I think team100 = blue)
    """
    tenmin_frame = match_info['timeline']['frames'][10]['participantFrames']
    team100_gold = [tenmin_frame[x]['totalGold'] for x in ['1', '2', '3', '4', '5'] ]
    team200_gold = [tenmin_frame[x]['totalGold'] for x in ['6', '7', '8', '9', '10'] ]
    
    return sum(team100_gold) - sum(team200_gold)