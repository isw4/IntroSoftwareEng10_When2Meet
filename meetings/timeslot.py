"""
Class to represent timeslots and perform some calculations
"""

import arrow, calc

ASCENDING = 1
DESCENDING = -1

class TimeSlot:

	def __init__(self, contains, begin_datetime, end_datetime):
		"""
		TimeSlot object, used to represent time slots. Contains
		the following fields:

		contains:	a list of dictionaries. Each dictionary contains information
					about the events that make up this timeslot. Fields of the
					dictionary are:
			summary:		Description of the event
			begin_datetime:	see below
			end_datetime:	see below
		begin_datetime:	isoformatted timedate string, about the date and time
						the merged event begins
		end_datetime:	isoformatted timedate string, about the date and time
						the merged event ends
		"""
		assert arrow.get(begin_datetime) < arrow.get(end_datetime)
		self.begin_datetime = begin_datetime
		self.end_datetime = end_datetime
		if isinstance(contains, str):
			self.contains = [ { 'summary': contains,
								'begin_datetime': begin_datetime,
								'end_datetime': end_datetime } ]
		else:
			self.contains = contains


	def merge(self, other):
		"""
		Tries to merge two TimeSlot objects. Normally used to merge two busy
		times.

		Args:
			other:   TimeSlot object, representing another busy time

		Returns:
			merged TimeSlot object, if it can be merged
			None, if it cannot be merged
		"""
		self_begin = arrow.get(self.begin_datetime)
		self_end = arrow.get(self.end_datetime)
		other_begin = arrow.get(other.begin_datetime)
		other_end = arrow.get(other.end_datetime)

		# Not Mergeable
		if self_end < other_begin or self_begin > other_end:
			return None

		# Mergable
		merged_contains = self.contains + other.contains
		if self_begin <= other_begin:
			merged_begin_datetime = self_begin.isoformat()
		else:
			merged_begin_datetime = other_begin.isoformat()

		if self_end >= other_end:
			merged_end_datetime = self_end.isoformat()
		else:
			merged_end_datetime = other_end.isoformat()

		return TimeSlot(merged_contains, merged_begin_datetime, merged_end_datetime)


	def find_freebusy_from(self, busylist):
		"""
		Finds a list of free times between the list of busy times. All busy
		times do not have to be merged.

		Args:
			self:		TimeSlot object, representing a single slot of free time
			busylist:	a list of TimeSlot objects, representing busy times
		
		Returns:
			a list of TimeSlot objects, representing free times
		"""
		#####
		# There maybe are busy events
		#####
		if busylist == []:
			# No busy events, entire free period is a free time
			return [ [self], [] ]

		#####
		# There are some busy events. Are they in the free period?
		#####
		free_begin = arrow.get(self.begin_datetime)
		free_end = arrow.get(self.end_datetime)

		# Eliminate events that end before or when the free period begins
		sorted_list = sort_by_end_time(busylist, DESCENDING)
		print('After first sort: {}'.format(sorted_list))
		reduced_list = []
		for busytime in sorted_list:
			if free_begin >= arrow.get(busytime.end_datetime):
				break
			# Append busy events that end after the free period begins
			reduced_list.append(busytime)
		if reduced_list == []:
			# All busy events end before the free period begins
			return [ [self], [] ]
		print('After first reduction: {}'.format(reduced_list))
		
		# Eliminate events that begin after or when the free period ends
		sorted_list = sort_by_begin_time(reduced_list, ASCENDING)
		print('After second sort: {}'.format(sorted_list))
		reduced_list = []
		for busytime in sorted_list:
			if free_end <= arrow.get(busytime.begin_datetime):
				break
			# Append busy events that start after the free period ends
			reduced_list.append(busytime)
		if reduced_list == []:
			# No busy events in the free period
			return [ [self], [] ]
		print('After second reduction: {}'.format(reduced_list))
		
		#####
		# There are some busy events in the free period. Finding free and busy times
		#####
		freetimes = [ ]
		busytimes = [ ]
		merged_list = calc.merge_single_list(reduced_list)
		print('Merged List: {}'.format(merged_list))
		
		for busytime in merged_list:
			busy_begin = arrow.get(busytime.begin_datetime)
			busy_end = arrow.get(busytime.end_datetime)

			if freetimes == []:
				# First busy entry
				print("This is the first entry")
				if free_begin >= busy_begin and free_end <= busy_end:
					# Special case of when the free period is completely within a busy time
					return [ [], [busytime] ]
				if free_begin < busy_begin:
					# If there is a block of free time between the start of the free period
					# and the start of the busy time, first append a complete block before 
					# appending a half block
					freetimes.append({ "begin_datetime": free_begin.isoformat(),
									   "end_datetime": busy_begin.isoformat() })
					print("Adding first entry. Free from {} to {}".format(free_begin.isoformat(), busy_begin.isoformat()))
					freetimes.append({ "begin_datetime": busy_end.isoformat(),
									   "end_datetime": None })
					print("Adding part of next entry. Free from {}".format(busy_end.isoformat()))
				else:
					# Otherwise, append a half block, waiting to be completed on next iteration
					freetimes.append({ "begin_datetime": busy_end.isoformat(),
									   "end_datetime": None })
					print("Adding part of first entry. Free from {}".format(busy_end.isoformat()))
				busytimes.append(busytime)
				continue

			# Subsequent entries. Finish the incomplete block from previous iteration, then
			# append another half block
			freetimes[len(freetimes)-1]["end_datetime"] = busy_begin.isoformat()
			print("to {}\n".format(busy_begin.isoformat()))
			freetimes.append({ "begin_datetime": busy_end.isoformat(),
							   "end_datetime": None })
			print("Adding part of next entry. Free from {}".format(busy_end.isoformat()))
			busytimes.append(busytime)

		# End for loop: finish loose ends
		# Busy time is after the free period, finish modifying free blocks of time
		if free_end > arrow.get(freetimes[len(freetimes)-1]["begin_datetime"]):
			# If the previous busy end time is before the free period end time,
			# then add the last block of free time
			freetimes[len(freetimes)-1]["end_datetime"] = free_end.isoformat()
			print("to {}(End)\n".format(free_end.isoformat()))
		else:
			# If not, there should not be another block of free time. Removes
			# the previously initiated block
			del freetimes[len(freetimes)-1]
			print("...Last entry cancelled")
		
		# Convert the list of free time dicts into list of TimeSlots
		fts = freetimes
		freetimes = [ ]
		for ft in fts:
			freetimes.append(TimeSlot('Free Time', ft['begin_datetime'], ft['end_datetime']))

		return [freetimes, busytimes]


	def serialize(self):
		""" To convert the object into something that can be sent to browser """
		return {
			'contains': self.contains,
			'begin_datetime': self.begin_datetime,
			'end_datetime': self.end_datetime
		}


	def equals(self, other):
		""" To be able to easily compare objects """
		if self.begin_datetime != other.begin_datetime \
		or self.end_datetime != other.end_datetime \
		or len(self.contains) != len(other.contains):
			return False
		for i in range(0, len(self.contains)):
			if self.contains[i]['summary'] != other.contains[i]['summary'] \
			or self.contains[i]['begin_datetime'] != other.contains[i]['begin_datetime'] \
			or self.contains[i]['end_datetime'] != other.contains[i]['end_datetime']:
				return False
		return True


	def __repr__(self):
		""" To be able to print object """
		c = None
		for event in self.contains:
			next_c = "'summary': '{}', 'begin_datetime': '{}', 'end_datetime': '{}'".format(event['summary'], event['begin_datetime'], event['end_datetime'])
			if c == None:
				c = '[{'+next_c+'}'
			else:
				c = c+', {'+next_c+'}'
		c += ']'
		s = "'begin_datetime': '{}', 'end_datetime': '{}', ".format(self.begin_datetime, self.end_datetime)
		return '{'+s+c+'}'


#################################################################################
#
# Helper Functions
#
#################################################################################

def sort_by_begin_time(timeslot_list, order):
	"""
	Sorts a list of merged TimeSlot objects by their begin_datetime
	"""
	assert order == ASCENDING or order == DESCENDING
	if order == ASCENDING:
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.begin_datetime[:-6].replace('T','').replace('-','').replace(':','')))
	else:
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.begin_datetime[:-6].replace('T','').replace('-','').replace(':','')), reverse=True)

def sort_by_end_time(timeslot_list, order):
	"""
	Sorts a list of merged TimeSlot objects by their end_datetime
	"""
	assert order == ASCENDING or order == DESCENDING
	if order == ASCENDING:
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.end_datetime[:-6].replace('T','').replace('-','').replace(':','')))
	else:
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.end_datetime[:-6].replace('T','').replace('-','').replace(':','')), reverse=True)


def serialize_list(timeslot_list):
	return [ts.serialize() for ts in timeslot_list]