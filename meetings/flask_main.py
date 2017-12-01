import flask
from flask import render_template, request, url_for, redirect, session

import json
import logging
import urllib

# Date/time and timezone handling 
import arrow # Replacement for datetime, based on moment.js
from dateutil import tz  # For interpreting local times

# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

# Mongo database
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Our own helper functions and classes
from from_gcal import list_calendars, list_instances_btwn_datetimes
from timeslot import TimeSlot
from db_func import DatabaseNav
import calc, timeslot


###
# Globals
###
import config
if __name__ == "__main__":
	CONFIG = config.configuration()
else:
	CONFIG = config.configuration(proxied=True)

####
# Flask setup
###
app = flask.Flask(__name__)
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key=CONFIG.SECRET_KEY

####
# Google API setup
###
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_KEY_FILE  ## You'll need this
APPLICATION_NAME = 'MeetMe class project'

####
# MongoDB setup
###
MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST, 
    CONFIG.DB_PORT, 
    CONFIG.DB)
print("Using Mongo URL: '{}'".format(MONGO_CLIENT_URL))
try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    collection = getattr(db, CONFIG.DB_COLLECTION)
    db_nav = DatabaseNav(collection)
except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)


#############################
#
#  Front Page
#
#############################

@app.route("/", methods=['GET', 'POST'])
def index():
	""" Front page. Directs to setting up a meeting if the user credentials are already valid """
	app.logger.debug('In index')
	return render_template('index.html')


#############################
#
#  Create Meeting Get/Posts
#
#############################

@app.route('/createmeeting/configure', methods=['GET', 'POST'])
def create_configure():
	""" Lets user configure the date and time range for the meeting he wants to arrange """
	app.logger.debug('In create_configure')
	if 'begin_datetime' not in session:
		init_session_values()

	app.logger.debug("Logging in...")
	credentials = get_credentials()
	if not credentials:
		session['next'] = url_for('create_configure')
		return redirect(url_for('authorize'))
	gcal_service = get_gcal_service(credentials)
	
	app.logger.debug("Got service. Getting Calendars")
	session['calendars'] = list_calendars(gcal_service)
	return render_template('create_configure.html')


@app.route('/createmeeting/selecttimes', methods=['GET', 'POST'])
def create_select_times():
	""" Gets date and time information and sets cookies for displaying next page """
	app.logger.debug("In create_configure with request: {}\n\nLogging in...".format(request.form))
	credentials = get_credentials()
	if not credentials:
		session['next'] = url_for('create_select_times')
		return redirect(url_for('authorize'))
	gcal_service = get_gcal_service(credentials)

	# Getting request data
	timezone = request.form.get('timezone')
	begin_time = request.form.get('begin_time')
	end_time = request.form.get('end_time')
	begin_date = request.form.get('daterange').split()[0]
	end_date = request.form.get('daterange').split()[2]
	duration = request.form.get('duration')
	app.logger.debug('duration: {}'.format(duration))
	selections = request.form.getlist("checkbox")

	# Update cookies
	session['daterange'] = request.form.get('daterange')
	session['duration'] = duration
	session['client_tz'] = timezone

	# Interpret client dates and times. All calculations henceforth are in the client's timezone.
	# This is necessary because of the way the free times for each date are determined. For each
	# date, a block of time is created. If the organizer is in a vastly different tz and the times
	# are calculated in the server time, there may be unexpected results
	session['begin_datetime'] = interpret_datetimetz(begin_date, begin_time, timezone)
	session['end_datetime'] = interpret_datetimetz(end_date, end_time, timezone)
	
	# Based on Calendar selections, calculating free times
	app.logger.debug("Calculating free times")
	raw_frees = calc.init_frees_by_date(session['begin_datetime'], session['end_datetime'])
	if not selections:
		app.logger.debug("No calendars selected. All times are free times")
		raw_busys = []
	else:
		app.logger.debug("Getting busy event instances from these selected calendars: {}".format(selections))
		raw_busys = list_instances_btwn_datetimes(gcal_service, selections, 
												  session['begin_datetime'], 
												  session['end_datetime'])
	session['freetimes'] = calc.free_times(raw_frees, raw_busys, duration)
	app.logger.debug('Free times are: {}'.format(session['freetimes']))
	return render_template('create_select_times.html')


@app.route('/createmeeting/sendinvites', methods=['GET', 'POST'])
def send_invites():
	""" 
	Inserts a meeting document in the db, then displays the invite mailto links for the inviter 
	to click, and his own link to check on the status of the meeting 
	"""
	app.logger.debug("In send_invites with request: {}".format(request.form))

	# Insert a meeting entry into the database
	raw_desc = request.form.get('description')
	emails = request.form.get('emails').split(',')
	raw_times = request.form.getlist('selected_freetimes')
	times = [ ]
	for raw_time in raw_times:
		parts = raw_time.split(',')
		times.append({
			'begin_datetime': parts[0],
			'end_datetime':   parts[1]
			})
	mtg_id = db_nav.insert_mtg(session['begin_datetime'], session['end_datetime'], session['duration'], emails, times, raw_desc)
	app.logger.debug("Meeting {} inserted into database".format(mtg_id))

	# Encoding links to check on or respond to meeting
	send = {}
	invitees = []
	result = db_nav.get_mtg_invites(mtg_id)
	send['inviter_link'] = url_for('check_status_get', mtg_id=result['mtg_id'], user_id=result['inviter_id'], _external=True)
	for invitee in result['invitees']:
		temp = {}
		temp['email'] = invitee['email']
		temp['link'] = url_for('respond_get', mtg_id=result['mtg_id'], user_id=invitee['id'], _external=True)
		invitees.append(temp)
	send['invitees'] = invitees
	
	# Encoding description into email body
	desc = '{} ... Click link below to respond to invitation:\n'.format(result['desc'])
	safe_desc = urllib.parse.quote(desc)
	send['desc'] = safe_desc
	
	session['send'] = send
	return render_template('send_invites.html')


#############################
#
#  Respond Meeting Get/Posts
#
#############################

@app.route('/respond/<string:mtg_id>/<string:user_id>', methods=['GET'])
def respond_get(mtg_id, user_id):
	""" Displays the meeting response page for a user if the ids are valid and the user has not yet responded """
	app.logger.debug("In respond_get with mtg:{} and user:{}".format(mtg_id, user_id))
	result = db_nav.get_invitee_data(mtg_id, user_id)
	app.logger.debug(result)
	if result == None:
		# Invalid mtg or user id
		return render_template('404.html')
	elif result == 'responded':
		# User has already responded
		return redirect(url_for('responded'))
	else:
		# User has not responded, so display page
		session['desc'] = enhance_description(result['begin_datetime'], result['end_datetime'], result['duration'], result['desc'])
		session['begin_datetime'] = result['begin_datetime']
		session['end_datetime'] = result['end_datetime']
		session['duration']  = result['duration']
		session['submit_route'] = url_for('respond_configure', mtg_id=mtg_id, user_id=user_id)
		return render_template('respond_index.html')


@app.route('/respond/configure/<string:mtg_id>/<string:user_id>', methods=['GET', 'POST'])
def respond_configure(mtg_id, user_id):
	""" Lets user configure the date and time range for the meeting he wants to arrange """
	app.logger.debug('In respond_configure. Logging in...')
	credentials = get_credentials()
	if not credentials:
		session['next'] = url_for('respond_configure', mtg_id=mtg_id, user_id=user_id)
		return redirect(url_for('authorize'))
	gcal_service = get_gcal_service(credentials)

	app.logger.debug("Got service. Getting Calendars")
	session['calendars'] = list_calendars(gcal_service)
	session['submit_route'] = url_for('respond_select_times', mtg_id=mtg_id, user_id=user_id)
	return render_template('respond_configure.html')


@app.route('/respond/selecttimes/<string:mtg_id>/<string:user_id>', methods=['GET', 'POST'])
def respond_select_times(mtg_id, user_id):
	""" Displays the user's free times calculated from the selected Calendars """
	app.logger.debug('In respond_select_times with request: {}'.format(request.form))
	credentials = get_credentials()
	if not credentials:
		session['next'] = url_for('respond_select_times', mtg_id=mtg_id, user_id=user_id)
		return redirect(url_for('authorize'))
	gcal_service = get_gcal_service(credentials)

	# Getting form data
	client_tz = request.form.get('timezone')
	selections = request.form.getlist('checkbox')
	
	# Based on Calendar selections, calculating free times
	app.logger.debug("Calculating free times")
	raw_frees = calc.init_frees_by_date(session['begin_datetime'], session['end_datetime'])
	if not selections:
		app.logger.debug("No calendars selected. All times are free times")
		raw_busys = []
	else:
		app.logger.debug("Getting busy event instances from these selected calendars: {}".format(selections))
		raw_busys = list_instances_btwn_datetimes(gcal_service, selections, 
												  session['begin_datetime'], 
												  session['end_datetime'])
	freetimes = calc.free_times(raw_frees, raw_busys, session['duration'])
	app.logger.debug('Free times are: {}'.format(freetimes))

	# Times are calculated in the organizer's timezone. But they should be displayed in the
	# user's current timezone.
	session['freetimes'] = []
	for ft in freetimes:
		temp = {}
		temp['begin_datetime'] = arrow.get(ft['begin_datetime']).to(client_tz).isoformat()
		temp['end_datetime'] = arrow.get(ft['end_datetime']).to(client_tz).isoformat()
		session['freetimes'].append(temp)
	
	session['submit_route'] = url_for('respond_submitted', mtg_id=mtg_id, user_id=user_id)
	return render_template('respond_select_times.html')


@app.route('/respond/submitted/<string:mtg_id>/<string:user_id>', methods=['GET', 'POST'])
def respond_submitted(mtg_id, user_id):
	""" 
	User just submitted a response. Gets the free times selected by the user and 
	stores it in the database 
	"""
	app.logger.debug('In respond_submitted with request: {}'.format(request.form))
	# Insert a meeting entry into the database
	raw_times = request.form.getlist('selected_freetimes')
	times = [ ]
	for raw_time in raw_times:
		parts = raw_time.split(',')
		times.append({
			'begin_datetime': parts[0],
			'end_datetime':   parts[1]
			})
	db_nav.set_invitee_freetimes(mtg_id, user_id, times)
	return render_template('submitted.html')


@app.route('/responded')
def responded():
	""" User already submitted a response """
	app.logger.debug('In responded')
	return render_template('responded.html')


#############################
#
#  Check Meeting Get/Posts
#
#############################

@app.route('/check/status/<string:mtg_id>/<string:user_id>', methods=['GET'])
def check_status_get(mtg_id, user_id):
	""" Lets the meeting organizer check the status of the meeting """
	app.logger.debug('In check_status_get')
	data = db_nav.get_inviter_data(mtg_id, user_id)
	if data == None:
		return render_template('404.html')

	session['invitees'] = data['invitees']
	session['duration'] = data['duration']
	session['desc'] = enhance_description(data['begin_datetime'], data['end_datetime'], data['duration'], data['desc'])
	session['freetimes'] = data['freetimes']
	session['submit_route'] = url_for('check_status_post', mtg_id=mtg_id, user_id=user_id)
	return render_template('check_status.html')


@app.route('/check/status/<string:mtg_id>/<string:user_id>', methods=['POST'])
def check_status_post(mtg_id, user_id):
	""" 
	Receives the data to confirm the meeting arrangement, then
	redirects to a page where the inviter can email all the invitees
	about the confirmed time
	"""
	app.logger.debug('In check_status_post with request: {}'.format(request.form))
	
	# Getting data from form
	i = int(request.form.get('radio'))
	selection = request.form.getlist('selection')[i]

	# Mailto recipients
	invites = db_nav.get_mtg_invites(mtg_id)
	emails = ''
	for invitee in invites['invitees']:
		emails += (invitee['email'] + ',')

	# Mailto description
	desc = 'Meeting has been arranged at {}({}GMT) for:\n\n{}'.format(humanize_datetime(selection), invites['timezone'], invites['desc'])
	safe_desc = urllib.parse.quote(desc)
	
	send = {}
	send['emails'] = emails
	send['desc'] = safe_desc
	session['send'] = send
	session['desc'] = invites['desc']
	db_nav.delete_mtg(mtg_id)
	return redirect(url_for('check_confirm'))


@app.route('/check/confirm')
def check_confirm():
	""" Lets inviter send an email to his invitees after confirming the meeting time"""
	app.logger.debug('In check_confirm')
	return render_template('check_confirm.html')


####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

@app.route("/authorize")
def authorize():
	"""
	A route for oauth2callback to come back to, which then redirects to a url defined 
	before the original call of this function
	"""
	credentials = get_credentials()
	if not credentials:
		app.logger.debug("Invalid/No credentials. Redirecting to authorization")
		return redirect(url_for('oauth2callback'))

	next_url = session.pop('next', url_for('index'))
	return redirect(next_url)


def get_credentials():
	"""
	Returns OAuth2 credentials if we have valid
	credentials in the session.  This is a 'truthy' value.
	Return None if we don't have credentials, or if they
	have expired or are otherwise invalid.  This is a 'falsy' value. 
	"""
	if 'credentials' not in session:
		return None

	credentials = client.OAuth2Credentials.from_json(session['credentials'])
	if (credentials.invalid or credentials.access_token_expired):
		return None

	return credentials


def get_gcal_service(credentials):
	"""
	We need a Google calendar 'service' object to obtain
	list of calendars, busy times, etc.  This requires
	authorization. If authorization is already in effect,
	we'll just return with the authorization. Otherwise,
	control flow will be interrupted by authorization, and we'll
	end up redirected back to /choose *without a service object*.
	Then the second call will succeed without additional authorization.
	"""
	app.logger.debug("Entering get_gcal_service")
	http_auth = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http_auth)
	app.logger.debug("Returning service")
	return service


@app.route('/oauth2callback')
def oauth2callback():
	"""
	The 'flow' has this one place to call back to.  We'll enter here
	more than once as steps in the flow are completed, and need to keep
	track of how far we've gotten. The first time we'll do the first
	step, the second time we'll skip the first step and do the second,
	and so on.
	"""
	app.logger.debug("Entering oauth2callback")
	flow =  client.flow_from_clientsecrets(
		CLIENT_SECRET_FILE,
		scope= SCOPES,
		redirect_uri=url_for('oauth2callback', _external=True))
	## Note we are *not* redirecting above.  We are noting *where*
	## we will redirect to, which is this function. 

	## The *second* time we enter here, it's a callback 
	## with 'code' set in the URL parameter.  If we don't
	## see that, it must be the first time through, so we
	## need to do step 1. 
	app.logger.debug("Got flow")
	if 'code' not in request.args:
		app.logger.debug("Code not in request.args")
		auth_uri = flow.step1_get_authorize_url()
		app.logger.debug(auth_uri)
		return redirect(auth_uri)
	## This will redirect back here, but the second time through
	## we'll have the 'code' parameter set
	else:
		## It's the second time through ... we can tell because
		## we got the 'code' argument in the URL.
		app.logger.debug("Code was in request.args")
		auth_code = request.args.get('code')
		credentials = flow.step2_exchange(auth_code)
		session['credentials'] = credentials.to_json()
		## Now I can build the service and execute the query,
		## but for the moment I'll just log it and go back to
		## the main screen
		app.logger.debug("Got credentials")
		return redirect(url_for('authorize'))


#############################
#
#  Error Handling
#
#############################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


####
#
#   Initialize session variables 
#
####

def init_session_values():
	"""
	Start with some reasonable defaults for date and time ranges.
	Note this must be run in app context ... can't call from main. 
	"""
	# Default date span = tomorrow to 1 week from now
	now = arrow.now('local')     # We really should be using tz from browser
	tomorrow = now.replace(days=+1)
	nextweek = now.replace(days=+7)
	session["daterange"] = "{} - {}".format(
		tomorrow.format("MM/DD/YYYY"),
		nextweek.format("MM/DD/YYYY"))
	# Default time span each day, 8 to 5
	session["begin_datetime"] = interpret_time("9am")
	session["end_datetime"] = interpret_time("5pm")


def interpret_datetimetz( date, time, timezone ):
	"""
	Read time in a human-compatible format and
	interpret as ISO format with local timezone.
	May throw exception if time can't be interpreted. In that
	case it will also flash a message explaining accepted formats.

	Args:
		date: 		str, in format MM/DD/YYYY
		time: 		str, in format HH:mm
		timezone:	str, client timezone in format ZZ (+-HH:mm)

	Returns:
		an isoformatted string of datetime in the client timezone
	"""
	app.logger.debug("Decoding date: '{}', time: '{}', and timezone: '{}'".format(date, time, timezone))
	dt_str = date + ' ' + time
	try:
		cl_arrow = arrow.get(dt_str, 'MM/DD/YYYY HH:mm').replace(tzinfo=timezone)
		app.logger.debug("Client time interpreted as: '{}'".format(cl_arrow.isoformat()))
	except:
		app.logger.debug("Failed to interpret time")
		raise
	return cl_arrow.isoformat()


def interpret_time( text ):
	"""
	Read time in a human-compatible format and
	interpret as ISO format with local timezone.
	May throw exception if time can't be interpreted. In that
	case it will also flash a message explaining accepted formats.
	"""
	app.logger.debug("Decoding time '{}'".format(text))
	time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
	try: 
		as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
		as_arrow = as_arrow.replace(year=2016) #HACK see below
		app.logger.debug("Succeeded interpreting time")
	except:
		
		flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
			  .format(text))
		raise
	return as_arrow.isoformat()
	#HACK #Workaround
	# isoformat() on raspberry Pi does not work for some dates
	# far from now.  It will fail with an overflow from time stamp out
	# of range while checking for daylight savings time.  Workaround is
	# to force the date-time combination into the year 2016, which seems to
	# get the timestamp into a reasonable range. This workaround should be
	# removed when Arrow or Dateutil.tz is fixed.
	# FIXME: Remove the workaround when arrow is fixed (but only after testing
	# on raspberry Pi --- failure is likely due to 32-bit integers on that platform


def enhance_description(iso_begin_datetime, iso_end_datetime, duration, raw_desc):
	"""
	Modifies the description to display information about the meeting configuration.
	Includes details about the start/end time, start/end date and meeting duration.
	"""
	begin_datetime = arrow.get(iso_begin_datetime)
	end_datetime = arrow.get(iso_end_datetime)
	duration = '{}hr {}min'.format(duration.split(':')[0], duration.split(':')[1])
	return '''The organizer would like to arrange for a {} meeting between the times {} and {}, from {} to {} (timezone:{}GMT). Event description:\n\n{}'''.format(
			duration,
			begin_datetime.format('h:mma'), end_datetime.format('h:mma'),
			begin_datetime.format('MM-DD-YYYY'), end_datetime.format('MM-DD-YYYY'),
			begin_datetime.format('ZZ'), raw_desc)


#################
#
# Functions used within the templates
#
#################


@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
	try: 
		normal = arrow.get( date )
		return normal.format("ddd MM/DD/YYYY")
	except:
		return "(bad date)"


@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
	try:
		normal = arrow.get( time )
		return normal.format("HH:mm")
	except:
		return "(bad time)"


@app.template_filter( 'html_datetime_compatible' )
def to_html_datetime( datetimeshift ):
	if ',' in datetimeshift:
		datetime = datetimeshift.split(',')[0]
		HH_mm = datetimeshift.split(',')[1]
		HH = int(HH_mm.split(':')[0])
		mm = int(HH_mm.split(':')[1])
		normal = arrow.get( datetime ).shift(hours=-HH, minutes=-mm)
	else:
		normal = arrow.get( datetimeshift )
	return normal.format('YYYY-MM-DDTHH:mm')


@app.template_filter( 'humanize_datetime' )
def humanize_datetime( datetime ):
	try:
		normal = arrow.get( datetime )
		return normal.format('ddd MM/DD/YYYY, h:mma')
	except:
		return datetime


@app.template_filter( 'humanize_time' )
def humanize_time( datetime ):
	try:
		normal = arrow.get( datetime )
		return normal.format('h:mma')
	except:
		return datetime


#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running under green unicorn)
  app.run(port=CONFIG.PORT,host="0.0.0.0")
	
