# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 10:21:47 2015

@author: Me
"""
import requests
import numpy as np
import itertools
import pdb

def load_featured_games( api_key, region = 'na'):
    """ Loads the game IDs of the "featured games"
    
        Argument:
        api_key: string of your api_key
        
        Returns:
        featured_game_ids: List of ints of game IDs
    """
    
    featured_url = 'https://' + region + '.api.pvp.net/observer-mode/rest/featured' + '?api_key=' + api_key
    featured_json = requests.get(featured_url).json()['gameList'] # load the url of featured games, and parse the JSON
    return featured_json
    
def get_summoners_IDs_from_featured_games(featured_json, api_key, region = 'na'):
    """
    Load the summoner names and summoner IDs from the featured game JSON
    
    Arguments:
    featured_json: JSON output of load_featured_games
    api_key: string of your api_key for the request
    
    Returns:
    participant_names
    """
    
    participants_json = np.array([x['participants'] for x in featured_json]).ravel() # get participants JSON for each game
    participant_names = [x['summonerName'] for x in participants_json] # strip out summoner names
    
    # get summoner IDs for the participants:
    
    summoner_ids = [get_summoner_ids_from_names(x, api_key, region) for x in list(urlify_string_list(participant_names)) ]
    
    summoner_ids = list(itertools.chain.from_iterable(summoner_ids)) # then flatten them
    
    return participant_names, summoner_ids

def get_summoner_ids_from_names(participant_names_single_string, api_key, region = 'na'):
    """ Returns the summoner ids for a list of summoner names
    """
    summoner_url = 'https://'+region + '.api.pvp.net/api/lol/' + region + '/v1.4/summoner/by-name/' + \
                    participant_names_single_string + '?api_key=' + api_key
                    
    summoner_info = requests.get(summoner_url).json()
    
    summoner_ids = [x['id'] for x in list(summoner_info.values())]
    return summoner_ids

def urlify_string_list(list_of_string):
    """ Takes a list of strings, and turns into a single, long, comma separated string for url comprehension
    """
    max_summoners = 40 # maximum number of summoners you can query at once with the
    for i in range(0, len(list_of_string), max_summoners):
        yield ','.join(list_of_string[i:i+max_summoners])

def make_matchlist_url_summoner_ID(cur_ID, solo_ranked_flag = True, season_flag = True, api_key, region = 'na'):
    """ Creates a request url for the given summoner ID, and the flags
    
    Arguments:
    list_IDs: a python list of summoner IDs (ints)
    solo_ranked_flag: whether to only get solo Queue games (when care about getting games for ML)
    season_flag: Whether to get games from only a particular season (for now, Season 2015)
    
    Returns: ??
    """
    if solo_ranked_flag:
        solo_ranked_string = 'rankedQueues=RANKED_SOLO_5x5&'
    else:
        solo_ranked_string = ''
        
        
    if season_flag:
        season_string = 'seasons=SEASON2015&'
    else:
        season_string = ''
        
    return 'https://' + region+ '.api.pvp.net/api/lol/' + region + '/v2.2/matchlist/by-summoner/' + \
                        str(cur_ID) + '?' + solo_ranked_string + season_string + 'api_key=' + api_key

def make_match_info_url(match_ID, timeline_flag, api_key, region = 'na'):
    if timeline_flag:
        timeline_string = 'includeTimeline=true&'
    else:
        timeline_string = ''
    return 'https://' + region + '.api.pvp.net/api/lol/' + region + '/v2.2/match/' + str(match_ID) + '?' + \
            timeline_string + 'api_key=' + api_key
    
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
def get_limited_request(request_url):
    return requests.get(request_url).json()
    