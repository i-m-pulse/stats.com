from stats_epl import EPLRequest
from config import Config

#Instantiate an EPL Class
EPL = EPLRequest(Config)

start_date = '2017-08-21'
end_date = '2017-08-27'
events_json = EPL.get_events(start_date, end_date)

#Enter stats.com event id for an on-going/completed EPL match
epl_event_id = '1913017'
specific_events_json = EPL.extract_event_details(epl_event_id)

print(events_json)
print(specific_events_json)