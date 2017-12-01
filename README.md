# CS322 Final Project: When2Meet
### Author: Isaac Hong Wong (iwong@uoregon.edu)
Last Updated: 30 Nov 2017

When2Meet is a minimal, privacy-conscious web application that helps users 
determine a common time to have a meeting. It requires all users to have a 
Google account, as it will read calendar data from Google Calendar. It also
requires the meeting organizer to have all the perticipant's email addresses.


## For Meeting Organizers

Requirements:
- Google account and Calendar
- Own email address(to send invitations)
- Email addresses of participants

Start setting up a meeting by visiting:
```
http://my_server_domain_name:my_port/
```

You will be given a link to check on the meeting status after setting up the
meeting. You can check on the response status of the participants, the free 
times that the responded participants have in common, and confirm a meeting time.
You will be able to confirm a meeting time even if not all the participants
have responded, but the email(by default) is sent to all participants regardless
of whether they have responded.


## For Participants

Requirements:
- Google account and Calendar

Respond to the invitation by clicking on the link in the email that you
were sent. Note that you can only respond to the invitation once.


## Privacy-consciousness
### Minimal data-stored
This application does not store user event details, calendars, or
even Google account email(unless it was provided by the organizer).
It only stores the free times that the user selects, and the user's
email address as provided by the organizer

### Data displayed
Organizer:
Can see: 
- Who has responded
- The free times that all responded participants have in common
Cannot see:
- The free times selected by any single participant

Participants:
Can See:
- Original date/time range the meeting was planned to be in
- Meeting duration
Cannot See:
- Free times selected by organizer
- Free times selected by other participants


## To set up the server

Requirements:
- Configured Google API key
- Configured MongoDB (recommend to host MongoDB at http://mlab.com)

### Setting up credentials file
Copy the credentials-skel file to the meetings folder
```
cp credentials-skil.ini meetings/credentials.ini
```

Edit credentials.ini
```
SECRET_KEY = put_a_random_string_here
```

### Configuring Google API Key
If you haven't already, you can get sign up/in to the Google API Console at:
https://console.developers.google.com/

Create new credentials by clicking: 
```
Credentials > Create credentials > OAuth client ID > Web Application
```

Name it whatever you want, but make sure to allow the redirect URI:
```
http://my_server_domain_name:my_port/oauth2callback
```

Download the json file of the credentials you just created, and copy it
into the meetings folder. Edit credentials.ini to add the path to your
json file.
```
GOOGLE_KEY_FILE = client_secret_123somehash456.apps.googleusercontent.com.json
```

### Configuring MongoDB(at Mlab)
If you haven't already, sign up for an account at http://mlab.com
If you don't want to use an existing database, create a new database and 
collection by clicking:
```
Create new
```

Select a location where your db will be based. The closer to where your
server is hosted, the better. Select a plan(free or paid), then name
your database. Submit the order.

Click on:
```
your_database > Collections > Add collection
```

Set a name, then click:
```
Users > Add database user
```

This will how your application logs into the database. Edit credentials.ini:
```
DB_USER = my_database_user_name
DB_USER_PW = my_database_user_password
DB_HOST = my_database_hostname (eg. ds123456.mlab.com)
DB_PORT = my_database_port (eg. 9001)
DB = my_database_name
DB_COLLECTION = my_collection_name
```

### Run
```
make install
make run
```