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


league_name = 'EPL'
SOCCER_BREAK_MINS = 15
FIRST_HALF_END_SOCCER_ID = 13


class EPLRequest:
    """ Stats.com EPL Request object"""
    def __init__(self, config):
        """ 
        config: object containing api_key, secret and endpoints
        """
        self.config = config
        self.api_key = config.API_KEY
        self.secret = config.SECRET
        self.api_host = config.API_HOST
        self.epl_events_path = config.EPL_EVENTS_PATH

        
    def get_events(self,start_date, end_date):
        """Get all events between a start data and end date
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
        events_path = self.epl_events_path 
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
        api_results = response_json.get('apiResults',"")
        league = api_results[0].get('league',"")
        season = league.get('season',"")
        event_type = season.get('eventType',"")
        matches = event_type[0].get('matches',"")
        
        match_array = []
        for match in matches:
            event_id = match.get('eventId',"")
            start_date_list = match.get('startDate')
            for start_date in start_date_list:
                date_type = start_date.get('dateType')
                if date_type == 'UTC':
                    start_time_utc = start_date.get('full',"")
            teams = match.get('teams')
            for team in teams:
                if (team.get('teamLocationType')).get('name') == 'home':
                    home_team_name = team.get('location',"") + " " + team.get('nickname',"")
                elif (team.get('teamLocationType')).get('name') == 'away':
                    away_team_name = team.get('location',"") + " " + team.get('nickname',"")
            match_dict =  {'event_id' : event_id, 'start_time_utc': start_time_utc, 'home_team_name': home_team_name,'away_team_name': away_team_name}  
            match_array.append(match_dict)
            match_json = json.dumps(match_array, sort_keys=True, indent=4)
        return match_json    

    def get_event_details(self, event_id):
        """Query the EPL Events API by event id
        Args:
            event_id (str): the stats.com event id for an EPL match.
        Returns:   
            dict: The JSON response from the request.
        """
        events_path = self.epl_events_path + event_id
        sig_e = str(self.api_key + self.secret + str(int(time.time()))).encode('utf-8')
        hash = hashlib.sha256()
        hash.update(sig_e)
        sig = hash.hexdigest()
        url = self.api_host + events_path + '?pbp=true&api_key=' + self.api_key + '&sig=' + sig
        print(u'Querying {0} ...'.format(url))
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.json()
									    
    def extract_event_details(self,event_id):
        """Extracts current score, event, player involved from the json response
        Args:
            event_id (str): the stats.com event id for an EPL match.
        Returns:   
            dict: dictionary containing:
                - league_name (str): League name
                - event_id (str): Event Id
                - event_status_name (str): Status of the match either "In Progress" or "Post Game"
                - start_time_utc (str, iso format): Start time of the match
                - current_period (str): Current period or last period if the game is over
                - current_time (object): Object contatining current_mins, current_secs and current_add_mins in the period
                - home_team_name (str): Home team name
                - away_team_name (str): Away team name
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
 
        api_results = response.get('apiResults',"")
        league = api_results[0].get('league',"")
        season = league.get('season',"")
        event_type = season.get('eventType',"")
        matches = event_type[0].get('matches',"")
    
        #Get current game status
        event_status = matches[0].get('eventStatus',"")
        event_status_id = event_status.get('eventStatusId',"")
        if event_status_id != 2 and event_status_id != 4:
            return 'Match has either not begun or has been postponed / cancelled'
        elif  event_status_id == 2:
            event_status_name = 'In Progress'
        elif event_status_id == 4:
            event_status_name = 'Post game'
            
        #Get start timestamp
        start_date_list = matches[0].get('startDate',"")
        for start_date in start_date_list:
            date_type = start_date.get('dateType',"")
            if date_type == 'UTC':
                start_time_utc = start_date.get('full',"")
        
        #Get current timestamp
        start_stats_timestamp = datetime.datetime.strptime(start_time_utc, "%Y-%m-%dT%H:%M:%S")
        epoch_start_time = calendar.timegm(start_stats_timestamp.utctimetuple())         
  
        #Get team names
        teams = matches[0].get('teams',"")
        for team in teams:
            if (team.get('teamLocationType')).get('name') == 'home':
                home_team_name = team.get('location',"") + " " + team.get('nickname',"")
            elif (team.get('teamLocationType')).get('name') == 'away':
                away_team_name = team.get('location',"") + " " + team.get('nickname',"")
                
        pbp_list = matches[0].get('pbp',"")
        pbp_list_trun = pbp_list[-10:]
        max_sequence_number = 0
        for pbp in pbp_list_trun:
            current_sequence_number = pbp.get('sequenceNumber')
            if current_sequence_number > max_sequence_number:
                max_sequence_number = current_sequence_number                
        
        for pbp in pbp_list_trun:
            if pbp.get('sequenceNumber') == max_sequence_number:
                current_period = pbp.get('period',"")
                current_time = pbp.get('time',"")
                current_mins = current_time.get('minutes',"")
                current_secs = current_time.get('seconds',"")
                current_add_mins = current_time.get('additionalMinutes', "")
                
                last_pbp_event = pbp.get('playEvent',"")
                last_pbp_event_id = last_pbp_event.get('playEventId',"")
                last_pbp_event_name = last_pbp_event.get('name',"")
                
                away_score_after = pbp.get('awayScore',"")
                home_score_after = pbp.get('homeScore',"")
                
                player_name = ''
                if 'offensivePlayer' in pbp:
                    player_name = pbp.get('offensivePlayer').get('displayName',"")
                if 'defensivePlayer' in pbp:
                    player_name = pbp.get('defensivePlayer').get('displayName',"")
                if 'replacedPlayer' in pbp:
                    player_name = pbp.get('replacedPlayer').get('displayName',"")
                if 'assistingPlayer' in pbp:
                    player_name = pbp.get('assistingPlayer').get('displayName',"")       
                   

        #Get venue details
        venue = matches[0].get('venue',"")
        venue_name = venue.get('name',"")
        venue_city = venue.get('city',"")
    
        dict = {"league_name" : league_name, "event_id" : event_id, "event_status" : event_status_name, "start_time_utc" : start_time_utc, "current_period" : current_period, "current_time" : current_time, "home_team_name" : home_team_name, "away_team_name" : away_team_name, "home_score_after" : home_score_after, "away_score_after" : away_score_after, "last_pbp_event_name" : last_pbp_event_name, "last_pbp_event_id" : last_pbp_event_id, "player_name" : player_name, "venue_name" : venue_name, "venue_city" : venue_city}
        response_json = json.dumps(dict, sort_keys=True, indent=4)
        return response_json
            
    def __repr__(self):
        print(self.config)