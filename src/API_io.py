# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 10:21:47 2015

@author: Me
"""
import requests
import numpy as np
import itertools
import pdb

def load_featured_games( api_key, region_key = 'na'):
    """ Loads the game IDs of the "featured games"
    
        Argument:
        api_key: string of your api_key
        
        Returns:
        featured_game_ids: List of ints of game IDs
    """
    
    api_dict = {'api_key': api_key}
    
    featured_url = 'https://' + region_key + '.api.pvp.net/observer-mode/rest/featured'
    featured_request = requests.get(featured_url, params = api_dict) # load the url of featured games, and parse the JSON
    return featured_request.json()['gameList']
    
def get_summoners_IDs_from_featured_games(featured_json, api_key, region_key = 'na'):
    """
    Load the summoner names from the featured game JSON. (This JSON has names and not IDs).
    Then send summonerNames to the API to get summoner IDs.
    
    Arguments:
    featured_json: JSON output of load_featured_games
    api_key: string of your api_key for the request
    
    Returns:
    summoner_names, summoner_IDs
    """
    
    participants_json = np.array([x['participants'] for x in featured_json]).ravel() # get participants JSON for each game
    summoner_names = [x['summonerName'] for x in participants_json] # strip out summoner names
    
    # get summoner IDs for the participants:
    chunked_names = list(urlify_string_list(summoner_names))
    summoner_ids = [get_summoner_ids_from_names(x, api_key, region_key) for x in chunked_names ]
    
    summoner_ids = list(itertools.chain.from_iterable(summoner_ids)) # flatten nested list
    
    return summoner_names, summoner_ids

def urlify_string_list(list_of_string):
    """ Takes a list of strings, and turns into a single, long, comma separated string for url comprehension.
        This is done because the Riot API only accepts 40 summoner names per query.
    """
    max_summoners = 40 # maximum number of summoners you can query at once with the
    for i in range(0, len(list_of_string), max_summoners):
        yield ','.join(list_of_string[i:i+max_summoners])

def get_summoner_ids_from_names(participant_names_single_string, api_key, region_key = 'na'):
    """ Returns the summoner ids for a list of summoner names
    """
    
    # create parameters for the request
    api_dict = {'api_key': api_key}
    base_url = 'https://{0}.api.pvp.net/api/lol/{0}/v1.4/summoner/by-name/{1}'
    summoner_url = base_url.format(region_key, participant_names_single_string)
                    
    summoner_info = requests.get(summoner_url, params = api_dict).json()
    
    summoner_ids = [x['id'] for x in list(summoner_info.values())]
    return summoner_ids

def make_matchhistory_url(summoner_ID, region_key = 'na'):
    """ Creates a url for passage to requests.get to get all matches by a single player.
        In use, should be combined with make_RIOT_request_params
    """
    base_url = 'https://{0}.api.pvp.net/api/lol/{0}/v2.2/matchlist/by-summoner/{1}'
        
    return base_url.format(region_key, summoner_ID)

def make_RIOT_request_params( api_key, solo_ranked_key = 'solo', season_year = False, timeline_flag = False, pre_str = ''):
    """ Creates a dictionary to pass to request.get containing parameters for whether we want ranked games,
        season, and the api_key
        
        Called in conjuction with urls made by make_matchlist_url_summoner_ID or make_match_info_url
    
    Arguments:
    solo_ranked_key: whether to get Solo Queue ('solo'), Team Ranked ('team'), or all games (False)
    season_year: if passed, season_year creates the correct string for the season parameter
        i.e. 3 -> SEASON3 #(2013)
             2014 -> SEASON2014
    pre_str: string whether to look at preseason ('PRE') or not ('')
    """
    
    request_param_dict = {'api_key': api_key}
    solo_team_dict = {'solo':'RANKED_SOLO_5x5', 'team':'RANKED_TEAM_5x5', 'builder':'TEAM_BUILDER_DRAFT_RANKED_5x5'}
    
    if solo_ranked_key:
        request_param_dict['rankedQueues'] = solo_team_dict[solo_ranked_key]  
    if season_year:
        request_param_dict['seasons'] = pre_str + 'SEASON' + str(season_year)
    if timeline_flag:
        request_param_dict['includeTimeline'] = 'true'
        
    return request_param_dict

def parse_match_json_for_matchIDs(match_histories, region_key):
    """ Loop through a list of JSONs, each of which is the match history for a single player.
    
    Returns: a numpy array list of int matchIDs
    """
    match_IDs = np.empty(0, dtype=int)
    for cur_matches in match_histories:
        if cur_matches['totalGames'] > 0: # for some summoners, for whatever reason, the totalGames will be 0
            match_IDs = np.append( match_IDs, [x['matchId'] for x in cur_matches['matches'] if x['region'] == region_key.upper()] )
    match_IDs = np.unique(match_IDs)
    return match_IDs.astype(np.int64)

def make_match_info_url(match_ID, region_key = 'na'):
    """ Creates a url for passage to requests.get to get all matches by a single player.
        In use, should be combined with make_RIOT_request_params
    """
        
    base_url = 'https://{0}.api.pvp.net/api/lol/{0}/v2.2/match/{1}'
    return base_url.format(region_key, match_ID)

import time
def rate_limited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate

@rate_limited(0.8)
def get_limited_request(request_url, request_params):
    num_tries = 10 # try a set number of times
    for i in range(num_tries):
        cur_request = requests.get(request_url, request_params)
        if cur_request.status_code == 200:
            return cur_request.json()
        else:
            time.sleep(1.2)
    print('Request failed after ' + str(num_tries) + ' tries.')
    
def get_master_challenger_Ids(api_key, region_key, solo_ranked_key = 'solo'):
    """ Query RIOT's league API to get list of summonderIds in Master's and Challenger
    
    """
        
    api_dict = make_RIOT_request_params(api_key,solo_ranked_key = 'solo')
    api_dict['type'] = api_dict.pop('rankedQueues') # different name for field in different request
    
    def get_league_ids(api_dict, region_key, challenger_or_master = 'challenger'):
        base_url = 'https://{0}.api.pvp.net/api/lol/{0}/v2.5/league/{1}'
        league_url = base_url.format(region_key, challenger_or_master)
        league_json = requests.get(league_url, params = api_dict).json()
        league_ids = [ x['playerOrTeamId'] for x in league_json['entries']]
        return league_ids
    
    challenger_ids = get_league_ids(api_dict, region_key, 'challenger')
    
    master_ids = get_league_ids(api_dict, region_key, 'master')
    
    challenger_ids.extend(master_ids)
    return challenger_ids