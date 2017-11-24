# proj8-Gcal
### Author: Isaac Hong Wong (iwong@uoregon.edu)
Grabs appointment data from a user's Google Calendar, and then displays
the busy and free times within a specified time range, for each of the 
dates within a specified date range


## How to use

1) Submit a specified time range, and then a specified date range
2) You will be redirected to a google authorization page to log in
3) Once authorized, select the calendars from which you want to extract
   busy times
4) Submit, and the busy times from those calendars within the time and
   date range will be displayed. The free times between those busy times
   will also be displayed


## How to set up the server

You will need a Google API key, and set it up to allow the redirect URI
```
http://my_server_ip:my_port/oauth2callback
```

1) Copy the credentials-skel file to the meetings folder
```
cp credentials-skil.ini meetings/credentials.ini
```

2) Download the Google client secrets file from the Google API, and
   reference the path from the credentials.ini file. Also set up any
   configuration variables as you see fit in the credentials.ini file

3) Run
```
make install
make run
```


## What are the busy times returned?


Will disregard:
	transparent events

Will include:
	All day events
	Events that span multiple days

Eg) If the time specified is 9am to 5pm, from 11/11 to 11/14(MM:DD),
    then the following events with times will be regarded as:

    | Times        | Is Busy
    | ---          | ---   
    | 7am to 8am   | False  
    | 7am to 10am  | True   
    | 10am to 11am | True   
    | 7am to 6pm   | True   
    | 4pm to 7pm   | True   
    | 7pm to 8pm   | False  

Eg) For events spanning multiple days:

    | Times                     | Is Busy
    | ---                       | ---	 
    | 11/11 7pm to 11/12 8am    | False  
    | 11/11 7pm to 11/12 10am   | True   