"""
Does some calculations not tied to the server
"""

import timeslot, arrow


def init_frees_by_date(iso_begin_datetime, iso_end_datetime):
	"""
	Initializes the free times that the user wants to query. The free TimeSlot objects
	all range in time from the HH:mm of iso_begin_datetime to the HH:mm of 
	iso_end_datetime, inclusive. Each TimeSlot corresponds to a date from the YYYY-MM-DD
	of iso_begin_datetime to the YYYY-MM-DD of iso_end_datetime, inclusive.

	Eg. begin_datetime: 2017-04-14T09:00, end_datetime: 2017-04-16T15:00
	then the returned value is a list of timeslots with the following begin and end:
	[{ 2017-04-14T09:00, 2017-04-14T15:00 },
	 { 2017-04-15T09:00, 2017-04-15T15:00 },
	 { 2017-04-16T09:00, 2017-04-16T15:00 }] 

	Args:
		iso_begin_datetime:	str, isoformatted datetime describing the begin date and time
		iso_end_datetime:	str, isoformatted datetime describing the end date and time

	Returns:
		A list of TimeSlot objects, representing the free times of each day
	"""
	begin_datetime = arrow.get(iso_begin_datetime)
	end_datetime = arrow.get(iso_end_datetime)
	
	curr_begin_datetime = begin_datetime
	curr_end_datetime = begin_datetime.replace(hour=int(end_datetime.format('HH')),
										  	   minute=int(end_datetime.format('mm')))
	avails = []
	while True:
		avails.append(timeslot.TimeSlot(curr_begin_datetime.isoformat(), curr_end_datetime.isoformat()))
		if curr_begin_datetime.format('YYYY-MM-DD') == end_datetime.format('YYYY-MM-DD'):
			break
		else:
			curr_begin_datetime = curr_begin_datetime.shift(days=+1)
			curr_end_datetime = curr_end_datetime.shift(days=+1)
	
	return avails


def free_times(raw_frees, raw_busys, duration):
	"""
	Returns the free times of a single user, calculated from the given time/date range,
	and the calendars selected by the user. The times of busy events in the selected 
	calendars will not be considered as free times. Free times less than the duration
	of the meeting will also not be returned

	Args:
		raw_frees:	list of TimeSlot objects, representing the raw free timeslots
		raw_busys:	list of TimeSlot objects, representing the raw busy times pulled
					from all the selected calendars. Accepts [] as an argument, if
					there were no selected calendars or no busy times in selected
					calendars
		duration:	str, h:mm of meeting duration

	Returns:
		A list of serialized timeslots dictionaries, containing:
			begin_datetime:	str, isoformatted datetime
			end_datetime:	str, isoformatted datetime
	"""
	result = []
	if raw_busys == []:
		# No busy times, so return raw free times as the resultant free times
		result = timeslot.serialize_list(raw_frees)
	else:
		# Has busy times, so calculate resultant free times.
		for free in raw_frees:
			# For the raw free time of each date, find the free times
			print('Trying {} to {}'.format(free.begin_datetime, free.end_datetime))
			freebusy = free.find_freebusy_from(raw_busys, duration)
			freetimes = freebusy[0]
			print('Free times: {}'.format(freetimes))
			sorted_ft = timeslot.sort_by_begin_time(freetimes, timeslot.ASCENDING)
			result.extend(timeslot.serialize_list(sorted_ft))
	return result

def merge_single_list(busylist):
	"""
	Merges the overlapping TimeSlots in the list of TimeSlots
	"""
	# Sorts the timeslots by start time
	sorted_list = timeslot.sort_by_begin_time(busylist, timeslot.ASCENDING)
	
	# TimeSlots that can no longer be merged with any of the other TimeSlots still
	# on the sorted_list.
	finalized_blobs = [ ]

	# A TimeSlot that still has the possibility of being merged with other TimeSlots
	# still on the sorted_list
	potential_blob = sorted_list[0]
	for i in range(1, len(sorted_list)):
		merged = potential_blob.merge(sorted_list[i])
		if merged == None:
			# Unable to merge
			finalized_blobs.append(potential_blob)
			potential_blob = sorted_list[i]
		else:
			# Merged
			potential_blob = merged

	# Endfor: finish loose ends
	finalized_blobs.append(potential_blob)
	return finalized_blobs


def intersect_two_lists(list_a, list_b):
	"""
	Finds the intersections between two lists of TimeSlots. Internally, each list 
	should not have any TimeSlots that intersect
	"""
	result = [ ]
	for item_a in list_a:
		for item_b in list_b:
			intersect = item_a.intersect(item_b)
			if intersect:
				result.append(intersect)

	return result