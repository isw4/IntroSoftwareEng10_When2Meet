"""
Class to represent timeslots and perform some calculations. This is a modified
version of the original timeslot class. Data stored about the events from the
user has been minimized, and other functions implemented.
"""

import arrow, calc

ASCENDING = 1
DESCENDING = -1

class TimeSlot:

	def __init__(self, begin_datetime, end_datetime):
		"""
		TimeSlot object, used to represent time slots. Contains
		the following fields:

		begin_datetime:	isoformatted timedate string, about the date and time
						the merged event begins
		end_datetime:	isoformatted timedate string, about the date and time
						the merged event ends
		"""
		assert arrow.get(begin_datetime) < arrow.get(end_datetime)
		self.begin_datetime = begin_datetime
		self.end_datetime = end_datetime


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
		if self_begin <= other_begin:
			merged_begin_datetime = self_begin.isoformat()
		else:
			merged_begin_datetime = other_begin.isoformat()

		if self_end >= other_end:
			merged_end_datetime = self_end.isoformat()
		else:
			merged_end_datetime = other_end.isoformat()

		return TimeSlot(merged_begin_datetime, merged_end_datetime)


	def intersect(self, other):
		"""
		Tries to find the intersection between two TimeSlot objects

		Args:
			other:   TimeSlot object, representing another busy time

		Returns:
			TimeSlot object, if there is an intersection
			None, if there is no intersection
		"""
		self_begin = arrow.get(self.begin_datetime)
		self_end = arrow.get(self.end_datetime)
		other_begin = arrow.get(other.begin_datetime)
		other_end = arrow.get(other.end_datetime)

		# No intersection
		if self_end <= other_begin or self_begin >= other_end:
			return None

		# Has an intersection
		if self_begin >= other_begin:
			intersect_begin_datetime = self_begin.isoformat()
		else:
			intersect_begin_datetime = other_begin.isoformat()

		if self_end <= other_end:
			intersect_end_datetime = self_end.isoformat()
		else:
			intersect_end_datetime = other_end.isoformat()

		return TimeSlot(intersect_begin_datetime, intersect_end_datetime)


	def find_freebusy_from(self, busylist, duration='00:00'):
		"""
		Finds a list of free times between the list of busy times. All busy
		times do not have to be merged. Free times that are < duration are
		eliminated.

		Args:
			self:		TimeSlot object, representing a single slot of free time
			busylist:	a list of TimeSlot objects, representing busy times
			duration:	str, HH:mm of the meeting duration
		
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
		dur_h = int(duration.split(':')[0])
		dur_m = int(duration.split(':')[1])
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
		print('duration: {}:{}'.format(dur_h, dur_m))
		for ft in fts:
			if arrow.get(ft['begin_datetime']).shift(hours=+dur_h, minutes=+dur_m) <= arrow.get(ft['end_datetime']):
				# the freetime can accomodate the meeting duration
				freetimes.append(TimeSlot(ft['begin_datetime'], ft['end_datetime']))

		return [freetimes, busytimes]


	def serialize(self):
		""" To convert the object into something that can be sent to browser """
		return {
			'begin_datetime': self.begin_datetime,
			'end_datetime': self.end_datetime
		}


	def equals(self, other):
		""" To be able to easily compare objects """
		if self.begin_datetime != other.begin_datetime or self.end_datetime != other.end_datetime:
			return False
		return True


	def __repr__(self):
		""" To be able to print object """
		s = "'begin_datetime': '{}', 'end_datetime': '{}', ".format(self.begin_datetime, self.end_datetime)
		return '{'+s+'}'


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