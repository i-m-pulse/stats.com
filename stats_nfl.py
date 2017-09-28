import hashlib
import hmac
import time
import datetime
import calendar
import json
import csv
import urllib
import requests
import sys
from config import Config


league_name = 'NFL'
FOOTBALL_PERIOD_MINS = 15
FOOTBALL_BREAK_MINS_QUARTER = 2
FOOTBALL_BREAK_MINS_HALF = 12
FOOTBALL_BREAK_EXTRA_MINS = 3


class NFLRequest:
    """ Stats.com NFL Request object"""
    def __init__(self, config):
        """ 
        config: object containing api_key, secret and endpoints
        """
        self.config = config
        self.api_key = config.API_KEY
        self.secret = config.SECRET
        self.api_host = config.API_HOST
        self.nfl_events_path = config.NFL_EVENTS_PATH

    def get_events(self,start_date, end_date):
        """Get all events within a particular start data and end date
        Args:
            startDate (str): YYYYMMDD or YYYY-MM-DD
            endDate (str): YYYYMMDD or YYYY-MM-DD
        Returns:
            List of events with following details:
            - event_id (str): stats.com id of the event
            - home_team_name (str)
            - away_team_name (str)
            - start_time_utc (str, iso format)
        """
        events_path = self.nfl_events_path 
        sig_e = str(self.api_key + self.secret + str(int(time.time()))).encode('utf-8')
        hash = hashlib.sha256()
        hash.update(sig_e)
        sig = hash.hexdigest()
        url = self.api_host + events_path + '?startDate=' + start_date + '&endDate=' + end_date + '&api_key=' + self.api_key + '&sig=' + sig
        print(u'Querying {0} ...'.format(url))
        response = requests.get(url)
        if response.status_code != 200:
            return None
        response_json = response.json()
        api_results = response_json.get('apiResults')
        league = api_results[0].get('league')
        season = league.get('season')
        event_type = season.get('eventType')
        events = event_type[0].get('events')
        event_array = []
        for event in events:
            event_id = event.get('eventId',"")
            start_date_list = event.get('startDate')
            for start_date in start_date_list:
                date_type = start_date.get('dateType')
                if date_type == 'UTC':
                    start_time_utc = start_date.get('full',"")
            teams = event.get('teams')
            for team in teams:
                if (team.get('teamLocationType')).get('name') == 'home':
                    home_team_name = team.get('location',"") + " " + team.get('nickname',"")
                elif (team.get('teamLocationType')).get('name') == 'away':
                    away_team_name = team.get('location',"") + " " + team.get('nickname',"")
            event_dict =  {'event_id' : event_id, 'start_time_utc': start_time_utc, 'home_team_name': home_team_name,'away_team_name': away_team_name}  
            event_array.append(event_dict)
            event_json = json.dumps(event_array, sort_keys=True, indent=4)
        return event_json
    
    def get_event_details(self, event_id):
        """Query the NFL Events API by event id
        Args:
            event_id (str): the stats.com event id for an NFL match.
        Returns:   
            dict: The JSON response from the request.
        """
        events_path = self.nfl_events_path + event_id
        sig_e = str(self.api_key + self.secret + str(int(time.time()))).encode('utf-8')
        hash = hashlib.sha256()
        hash.update(sig_e)
        sig = hash.hexdigest()
        url = self.api_host + events_path + '?pbp=true&api_key=' + self.api_key + '&sig=' + sig
        #print(u'Querying {0} ...'.format(url))
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.json()
    
    def extract_event_details(self,event_id):
        """Extracts current score, event, player involved from the json response
        Args:
            event_id (str): the stats.com event id for an NFL match.
        Returns:   
            dict: dictionary containing:
                - league_name (str): League name
                - event_id (str): Event Id
                - event_status_name (str): Status of the match either "In Progress" or "Post Game"
                - start_time_utc (str, iso format): Start time of the match
                - current_period (str): Current period or last period if the game is over
                - current_time (str): Time remaining in the current period
                - home_team_name (str): Home team name
                - away_team_name (str): Away team name
                - home_score_before (str): Home team score before last play by play event
                - away_score_before (str): Away team score before last play by play event
                - home_score_after (str): Home team score after last play by play event
                - away_score_after (str): Away team score after last play by play event
                - last_pbp_event_name (str): Name of the last play by play event
                - last_pbp_event_id (str): ID of the last play by play event
                - player_name (str): Player involved in last play by play event
                - venue_name (str): Match venue name
                - venue_city (str): Match venue city          
        """
        response = self.get_event_details(event_id)
        if response == None:
            return 'No response received, check event id'
 
        api_results = response.get('apiResults')
        league = api_results[0].get('league')
        season = league.get('season')
        event_type = season.get('eventType')
        events = event_type[0].get('events')
    
        #Get current game status
        event_status = events[0].get('eventStatus')
        event_status_id = event_status.get('eventStatusId',"")
        if event_status_id != 2 and event_status_id != 4:
            return 'Match has either not begun or has been postponed / cancelled'
        elif  event_status_id == 2:
            event_status_name = 'In Progress'
        elif event_status_id == 4:
            event_status_name = 'Post game'
            
        start_date_list = events[0].get('startDate')
        for start_date in start_date_list:
            date_type = start_date.get('dateType')
            if date_type == 'UTC':
                start_time_utc = start_date.get('full',"")
  
        teams = events[0].get('teams')
        for team in teams:
            if (team.get('teamLocationType')).get('name') == 'home':
                home_team_name = team.get('location',"") + " " + team.get('nickname',"")
            elif (team.get('teamLocationType')).get('name') == 'away':
                away_team_name = team.get('location',"") + " " + team.get('nickname',"")
    
        if event_status_id == 2: 
            last_play = events[0].get('lastPlay')
        elif event_status_id == 4:
            pbp_list = events[0].get('pbp')
            pbp_list_trun = pbp_list[-10:]
            max_play_id = 0
            for pbp in pbp_list_trun:
                current_play_id = pbp.get('playId')
                if current_play_id > max_play_id:
                    max_play_id = current_play_id  
            for pbp in pbp_list_trun:
                if pbp.get('playId') == max_play_id:
                    last_play = pbp
                
        current_period = last_play.get('period',"")
        current_time = last_play.get("time","")
        away_score_before = last_play.get('awayScoreBefore',"")
        away_score_after = last_play.get('awayScoreAfter',"")
        home_score_before = last_play.get('homeScoreBefore',"")
        home_score_after = last_play.get('homeScoreAfter',"")
        if (away_score_after - away_score_before == 6) or (home_score_after - home_score_before == 6):
            last_pbp_event = last_play.get('playType')
            last_pbp_event_id = last_pbp_event.get('playTypeId',"")
            last_pbp_event_name = last_pbp_event.get('name',"") + " Touchdown"
        else:
            last_pbp_event = last_play.get('playType')
            last_pbp_event_id = last_pbp_event.get('playTypeId',"")
            last_pbp_event_name = last_pbp_event.get('name',"")
        
            players_involved_list = last_play.get('playersInvolved')
            player_name = ''
            for players_involved in players_involved_list:
                type_sequence = players_involved.get('typeSequence')
                player_involved_type = players_involved.get('playerInvolvedType')
                player = players_involved.get('player')
                if type_sequence == 1 and player_involved_type == 'player':
                    player_name = player.get('firstName',"") + " " + player.get('lastName',"")
           
        #Get venue details
        venue = events[0].get('venue')
        venue_name = venue.get('name',"")
        venue_city = venue.get('city',"")
    
        dict = {"league_name" : league_name, "event_id" : event_id, "start_time_utc" : start_time_utc, "current_period" : current_period, "current_time" : current_time, "home_team_name" : home_team_name, "away_team_name" : away_team_name, "home_score_before" : home_score_before, "home_score_after" : home_score_after, "away_score_before" : away_score_before, "away_score_after" : away_score_after, "last_pbp_event_name" : last_pbp_event_name, "last_pbp_event_id" : last_pbp_event_id, "player_name" : player_name, "venue_name" : venue_name, "venue_city" : venue_city}
        response_json = json.dumps(dict, sort_keys=True, indent=4)
        return response_json
    
    def __repr__(self):
        print(self.config)
        