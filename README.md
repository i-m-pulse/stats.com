# stats.com events library
Current scores &amp; events for NFL &amp; EPL matches from stats.com

## Overview
Script to fetch match details like current score, play by play event, player & team information for NFL & EPL leagues from stats.com Events API. 
Refer STATS documentation here: http://developer.stats.com/page

## Installation

1. Install a virtual environment of your choice

2. Execute
``` pip install -r requirements.txt ```

3. Edit the config.py with your API Key and Secret.

4. Methods to use:
    - Use get_events method to get all events between the specified dates
    - Use get_event_details method to get the full JSON response from stats.com events API
    - Use extract_event_details method to get current score, play by play events, team information from events API

5. Try it!
``` python run_nfl.py ``` for NFL
``` python run_epl.py ``` for EPL

Cheers!
