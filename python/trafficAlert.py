import json
import time
import datetime
import urllib.request
import re
import requests

# A python3 script that checks drive time to a destination and, based on thresholds you hardcode (I know, I know) below, lights your Hue device accordingly

# Set up the API Keys for later
gMapsApiKey = "your key here"
hueApiKey = "your key here"

# Set up the Origin and Destination for the drive - addresses (properly URL encoded) work well
origin = "your starting point"
destination = "your ending point"

# Get the current time, as you need to pass that into the GMaps API...and we'll use it for logging
epoch_time = int(time.time())
print (time.asctime( time.localtime(time.time()) ) + ": Getting traffic data")

# Prep the request
req = urllib.request.Request(
        "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=" + origin +
        "&destinations=" + destination + "&departure_time=" + str(epoch_time) +
        "&traffic_model=best_guess&key=" + gMapsApiKey,
        data=None,
        headers={
                  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                }
        )

# Make the request
f = urllib.request.urlopen(req, timeout=2)
# Stuff the result into a JSON object
json_obj = json.loads(f.read().decode('utf-8'))
# extract the drive time - returns things like "47 mins"
commute_time = json_obj['rows'][0]['elements'][0]['duration_in_traffic']['text']
# strip the cruft away; keep only the numeric part
commute_min = int(re.search(r'\d+', commute_time).group())
# OK, we're done with the traffic info
print (time.asctime( time.localtime(time.time()) ) + ": Traffic data received")

now = datetime.datetime.now()
# the script is scheduled for a last run at 03:55 (6:55 AM ET), so let's turn the light off
if (now.hour == 3) and (now.minute >= 55):
    # this block is a little inefficient because I'm still setting a new_hue just so the code below doesn't die - will refactor this someday
    print("Time is now " + now.strftime('%c') + ". Time to stop checking traffic. Turning the light off.")
    payload = "{\"on\":false}"
    new_hue = 25500
# pick your own pain thresholds, obviously!
elif commute_min < 51:
    # All (mostly) clear - let's go green!
    print("Traffic is OK; commute time is " + str(commute_min) + " minutes.")
    payload = "{\"on\":true, \"sat\":254, \"hue\":25500, \"bri\":160}"
    new_hue = 25500
elif (commute_min >= 51) and (commute_min < 60):
    # Eh. A little slow. Orange like an Oompa Loompa.
    print("Traffic isn't great; commute time is " + str(commute_min) + " minutes.")
    payload = "{\"on\":true, \"sat\":254, \"hue\":7482, \"bri\":160}"
    new_hue = 7482
else:
    # You're gonna have a bad time... Red.
    print("Traffic is bad; commute time is " + str(commute_min) + " minutes.")
    payload = "{\"on\":true, \"sat\":254, \"hue\":65280, \"bri\":160}"
    new_hue = 65280

# first find out if we're keeping the same color - if so, we're going to blink the lights,
#    just so we let everyone know we're still doing our job and haven't gotten stuck.

# Get info on the lightstrip (which is #3 in my house)
# Use the IP of your Hue Bridge here
r = requests.get('http://192.168.0.42/api/' + hueApiKey + '/lights/3')
# Stuff the result into a JSON object
current_state_json_obj = json.loads(r.text)
# Go get the current value of 'hue' - this is only used to determine if the color isn't changing and is used below
old_hue = current_state_json_obj['state']['hue']

# Set the new color of the lightstrip
r = requests.put('http://192.168.0.42/api/' + hueApiKey + '/lights/3/state', data=payload)
# If we're just sustaining the same color, blink to show we're alive
if (new_hue == old_hue):
    payload = "{\"alert\":\"select\"}"
    r = requests.put('http://192.168.0.42/api/' + hueApiKey + '/lights/3/state', data=payload)

