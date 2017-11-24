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
		iso_begin_datetime:	str, isoformatted datetime describing the end date and time
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
		avails.append(timeslot.TimeSlot('Free Time', curr_begin_datetime.isoformat(), curr_end_datetime.isoformat()))
		if curr_begin_datetime.format('YYYY-MM-DD') == end_datetime.format('YYYY-MM-DD'):
			break
		else:
			curr_begin_datetime = curr_begin_datetime.shift(days=+1)
			curr_end_datetime = curr_end_datetime.shift(days=+1)
	
	return avails


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