"""
Module that requests information from Google Calendars. All the main functions require a valid google calendar service.
Get the user credentials, build the service, and then pass the service into the functions along with any other required
parameters.

Main Functions:
list_calendars						: lists all of a user calendars
list_instances_between_datetimes	: lists all event instances from selected calendars that are not transparent,
									  and between a start and end datetime

Helper Functions:
cal_sort_key
to_timeslot
"""

import arrow
from dateutil import tz
from timeslot import TimeSlot

#############################
#
#  Main Functions
#
#############################

def list_calendars(service):
	"""
	Given a google 'service' object, return a list of
	calendars.  Each calendar is represented by a dict.
	The returned list is sorted to have
	the primary calendar first, and selected (that is, displayed in
	Google Calendars web app) calendars before unselected calendars.

	Args:
		service:		Google Calendar service

	Returns:
		a list of dictionaries, with relevant information about all
		the user Calendars
	"""
	print("Listing calendars from Google Calendar")  
	calendar_list = service.calendarList().list().execute()["items"]
	result = []
	for cal in calendar_list:
		# Optional binary attributes with False as default
		selected = ("selected" in cal) and cal["selected"]
		primary = ("primary" in cal) and cal["primary"]

		result.append(
		  { "kind": cal["kind"],
			"id": cal["id"],
			"summary": cal["summary"],
			"selected": selected,
			"primary": primary,
			})
	
	return sorted(result, key=cal_sort_key)


def list_instances_btwn_datetimes(service, selected_cal, begin_datetime, end_datetime):
	"""
	Given a google 'service' object and a list of calendar IDs, returns a list of 
	event instances that fall between the given time range on each date within the 
	given date range. The times are also returned in the server's timezone

	Args:
		service:		Google Calendar service
		selected_cal:	a list of Calendar ids that the user has selected
		begin_datetime:	the min datetime from which to pull events
		end_datetime:	the max datetime from which to pull events

	Returns:
		a list of TimeSlot objects, created from the instances returned from Google
	"""
	print("Getting Google Calendar events from selected calendars")
	timezone = arrow.get(begin_datetime).format('ZZ') # Client's timezone
	result = []
	for cal_id in selected_cal:
		# Getting all event instances that fall within a datetime frame for each selected calendar
		instances = service.events().list(calendarId=cal_id, singleEvents=True, 
										  timeMin=begin_datetime, timeMax=end_datetime, 
										  timeZone=timezone).execute()
		for instance in instances['items']:
			# Ignores transparent events
			if "transparency" in instance and instance["transparency"] == "transparent":
				continue

			instance = to_timeslot(instance)
			result.append(instance)
	
	print("All busy instances found: {}".format(result))
	return result


#############################
#
#  Helper Functions
#
#############################


def cal_sort_key( cal ):
	"""
	Sort key for the list of calendars:  primary calendar first,
	then other selected calendars, then unselected calendars.
	(" " sorts before "X", and tuples are compared piecewise)
	"""
	if cal["selected"]:
	   selected_key = " "
	else:
	   selected_key = "X"
	if cal["primary"]:
	   primary_key = " "
	else:
	   primary_key = "X"
	return (primary_key, selected_key, cal["summary"])
			

def to_timeslot(instance):
	"""
	Creates a timeslot object from a Google Calendar event instance.

	Args:
		instance:	dict, a google calendar dict

	Returns:
		a dict with only relevant key value pairs
	"""
	if 'dateTime' in instance['start']:
		# Instance has a start and end time
		begin_datetime = instance['start']['dateTime']
		end_datetime   = instance['end']['dateTime']
	elif 'date' in instance['start']:
		# Without a start and end time: is an all day event
		begin_datetime = arrow.get(instance['start']['date']).replace(hour=00,
																	  minute=00,
																	  tzinfo=tz.tzlocal()
																	  ).isoformat()
		end_datetime   = arrow.get(instance['end']['date']).replace(hour=00,
																	minute=00,
																	tzinfo=tz.tzlocal()
																	).isoformat()
	else:
		# This case shouldn't happen
		print("Instance has no specified start and end time or date")
		assert False

	return TimeSlot(instance['summary'], begin_datetime, end_datetime)