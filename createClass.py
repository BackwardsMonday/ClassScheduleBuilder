from __future__ import print_function
from asyncio import events
from calendar import weekday


import os.path

from datetime import datetime, timezone, timedelta, date, time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re

#IMPORTANT: if this is true program will delete ALL events on callander
shouldDelete = True
#If false, no events will be created
shouldCreate = True
daysToSearch = 140
#Idealy contains regex instead of spaces or cammel case; eg "b.*day"
requieredEvent = "b.*day"
checkForEarly = True
checkForAssembly = True
#Should be a string containg an ordianal number; eg "1st"
period = "1st"
seminaryCalanderId = "topgs9fo3mi8p975dlo59c48h4@group.calendar.google.com"

def getCreds():
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/media/daymon/ESD-USB/repos/googleCalanderSyminaryImport/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def delEvents(service, todayAllDay):
    seminaryCalanderEventsResult = service.events().list(calendarId=seminaryCalanderId, timeMin=todayAllDay.isoformat()+"Z").execute()
    seminaryCalanderEvents = seminaryCalanderEventsResult.get('items', [])
    print("Finding events to delete")
    if seminaryCalanderEvents:
        print("Events found")
        for event in seminaryCalanderEvents:
            print(event["id"])
            service.events().delete(calendarId=seminaryCalanderId, eventId=event["id"]).execute()
            print("Event deleted")

def createEvents(service, todayAllDay, seminaryEvent, seminaryTimes):
    for i in range(daysToSearch):
        early = False
        allDay = (todayAllDay+timedelta(days=i)).isoformat() + 'Z'
        endAllDay = (todayAllDay+timedelta(days=i, seconds=1)).isoformat() + 'Z'
        dayOfWeek = (todayAllDay+timedelta(days=i)).weekday()
        events_result = service.events().list(calendarId='708@wsd.net', timeMin=allDay,
                                                timeMax=endAllDay,
                                                maxResults=10, singleEvents=True,
                                                orderBy='startTime').execute()
        
        events = events_result.get('items', [])
        if not events:
            print('No upcoming events found.')
            continue

        print(dayOfWeek)

        
        summaryList = [event['summary'].strip().lower() for event in events]
        print(summaryList)
        if any(re.search(requieredEvent.lower(), summary) for summary in summaryList):
            print(f"{requieredEvent} found")
            if checkForEarly:
                print("checking for early")
                if any(re.search("early.*out", summary) for summary in summaryList):
                    early = True
                    seminaryEvent["start"]["dateTime"] = (seminaryTimes[period][5]["start"]+timedelta(days=i)).isoformat()
                    seminaryEvent["end"]["dateTime"] = (seminaryTimes[period][5]["end"]+timedelta(days=i)).isoformat()
                    seminaryEvent["summary"]="Seminary EARLY"
            if not early:
                seminaryEvent["start"]["dateTime"]= (seminaryTimes[period][dayOfWeek]["start"]+timedelta(days=i)).isoformat()
                seminaryEvent["end"]["dateTime"]= (seminaryTimes[period][dayOfWeek]["end"]+timedelta(days=i)).isoformat()
                seminaryEvent["summary"]="Seminary"
            if checkForAssembly:
                if any("assembly" in summary for summary in summaryList):
                    seminaryEvent["summary"] += " ASSEMBLY"
                    seminaryEvent["description"] = "Due to the assembly, start and end time may be off."
                    

            service.events().insert(calendarId=seminaryCalanderId,body=seminaryEvent).execute()
            print("event created")
        elif "aday" in summaryList:
            print("event not created: A day")
        # for event in events:
        #     start = event['start'].get('dateTime', event['start'].get('date'))
        #     print(start, event['summary'])

def main():
    creds = getCreds()
    seminaryEvent = {
        'summary': 'Seminary',
        'location': '2270 W 4800 S, Roy, UT 84067',
        "reminders": {
            "useDefault":False,
            "overrides": [
                {
                    "method":"popup",
                    "minutes": 15
                }
            ]
        },
        "start": {
            "dateTime": datetime.strftime(datetime.now(timezone(-timedelta(hours=8))),"%Y-%m-%dT%H:%M:%S%z"),
            "timeZone": "America/Boise"
        },
        "end": {
            "dateTime": datetime.strftime(datetime.now(timezone(-timedelta(hours=4)))+timedelta(hours=4),"%Y-%m-%dT%H:%M:%S%z"),
            "timeZone": "America/Boise"
        }
    }
    


    service = build('calendar', 'v3', credentials=creds)
    #events_result = service.events().insert(calendarId="topgs9fo3mi8p975dlo59c48h4@group.calendar.google.com",body=event).execute()
    # Call the Calendar API 2015-05-28T09:00:00-07:00
        # Call the Calendar API
    todayAllDay = datetime.utcnow()
    today = date.today()
    seminaryTimes = {
        "1st":[
            #monday
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=9, minute=5)),
            },
            #tuesday
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=9, minute=5)),
            },
            #wensday
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=9, minute=5)),
            },
            #thursday
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=9, minute=5)),
            },
            #friday
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=9, minute=5)),
            },
            #early
            {
                "start": datetime.combine(today, time(hour=7, minute=45)), 
                "end": datetime.combine(today, time(hour=8, minute=45)),
            },
        ],
        "2nd":[
            #monday
            {
                "start": datetime.combine(today, time(hour=9, minute=10)), 
                "end": datetime.combine(today, time(hour=9, minute=35)),
            },
            #tuesday
            {
                "start": datetime.combine(today, time(hour=9, minute=10)), 
                "end": datetime.combine(today, time(hour=9, minute=35)),
            },
            #wensday
            {
                "start": datetime.combine(today, time(hour=9, minute=10)), 
                "end": datetime.combine(today, time(hour=9, minute=35)),
            },
            #thursday
            {
                "start": datetime.combine(today, time(hour=9, minute=10)), 
                "end": datetime.combine(today, time(hour=9, minute=35)),
            },
            #friday
            {
                "start": datetime.combine(today, time(hour=9, minute=10)), 
                "end": datetime.combine(today, time(hour=9, minute=35)),
            },
            #early
            {
                "start": datetime.combine(today, time(hour=8, minute=50)), 
                "end": datetime.combine(today, time(hour=9, minute=45)),
            },
        ],
        "3rd":[
            #monday
            {
                "start": datetime.combine(today, time(hour=11, minute=50)), 
                "end": datetime.combine(today, time(hour=13, minute=10)),
            },
            #tuesday
            {
                "start": datetime.combine(today, time(hour=11, minute=50)), 
                "end": datetime.combine(today, time(hour=13, minute=10)),
            },
            #wensday
            {
                "start": datetime.combine(today, time(hour=11, minute=50)), 
                "end": datetime.combine(today, time(hour=13, minute=10)),
            },
            #thursday
            {
                "start": datetime.combine(today, time(hour=11, minute=50)), 
                "end": datetime.combine(today, time(hour=13, minute=10)),
            },
            #friday
            {
                "start": datetime.combine(today, time(hour=11, minute=50)), 
                "end": datetime.combine(today, time(hour=13, minute=10)),
            },
            #early
            {
                "start": datetime.combine(today, time(hour=9, minute=50)), 
                "end": datetime.combine(today, time(hour=10, minute=45)),
            },
        ],
        "4th":[
            #monday
            {
                "start": datetime.combine(today, time(hour=13, minute=15)), 
                "end": datetime.combine(today, time(hour=14, minute=30)),
            },
            #tuesday
            {
                "start": datetime.combine(today, time(hour=13, minute=15)), 
                "end": datetime.combine(today, time(hour=14, minute=30)),
            },
            #wensday
            {
                "start": datetime.combine(today, time(hour=13, minute=15)), 
                "end": datetime.combine(today, time(hour=14, minute=30)),
            },
            #thursday
            {
                "start": datetime.combine(today, time(hour=13, minute=15)), 
                "end": datetime.combine(today, time(hour=14, minute=30)),
            },
            #friday
            {
                "start": datetime.combine(today, time(hour=13, minute=15)), 
                "end": datetime.combine(today, time(hour=14, minute=30)),
            },
            #early
            {
                "start": datetime.combine(today, time(hour=10, minute=50)), 
                "end": datetime.combine(today, time(hour=11, minute=45)),
            },
        ]
        
    }
    if shouldDelete:
        delEvents(service, todayAllDay)
    if shouldCreate:
        createEvents(service, todayAllDay, seminaryEvent, seminaryTimes)
    

if __name__ == '__main__':
    main()