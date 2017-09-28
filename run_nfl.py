from stats_nfl import NFLRequest
from config import Config

#Instantiate an EPL Class
NFL = NFLRequest(Config)

start_date = '2017-08-21'
end_date = '2017-08-27'
events_json = NFL.get_events(start_date, end_date)

#Enter stats.com event id for an on-going/completed NFL match
nfl_event_id = '1744715'
specific_events_json = NFL.extract_event_details('1744715')

print(events_json)
print(specific_events_json)