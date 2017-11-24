import arrow

ASCENDING = 1
DESCENDING = -1

class TimeSlot:

	def __init__(self, summary, begin_datetime, end_datetime):
		"""
		TimeSlot object, used to represent time slots. Contains
		the following fields:

		summary:	list of strings, describes the event occupying the time
					slot. May contain information about the owner, the event
					title, times, etc
		begin_datetime:	isoformatted timedate string, about the date and time
						the event begins
		end_datetime:	isoformatted timedate string, about the date and time
						the event ends
		"""
		assert arrow.get(begin_datetime) < arrow.get(end_datetime)
		self.summary = summary
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
		merged_summary = self.summary
		for each in other.summary:
			merged_summary.append(each)

		if self_begin <= other_begin:
			merge_begin_datetime = self_begin.isoformat()
		else:
			merge_begin_datetime = other_begin.isoformat()

		if self_end >= other_end:
			merge_end_datetime = self_end.isoformat()
		else:
			merge_end_datetime = other_end.isoformat()

		return TimeSlot(merged_summary, merge_begin_datetime, merge_end_datetime)


	def find_freebusy_from(self, busylist):
		"""
		Finds a list of free times between the list of busy times. All busy
		times in the list should already be merged.

		Args:
			self:		TimeSlot object, representing a single slot of free time
			busylist:	a list of TimeSlot objects, representing busy times
		
		Returns:
			a list of TimeSlot objects, representing free times
		"""
		# There maybe are busy events
		if busylist == []:
			# No busy events, entire free period is a free time
			return [ [self], [] ]

		# There are busy events. Are they in the free period?
		free_begin = arrow.get(self.begin_datetime)
		free_end = arrow.get(self.end_datetime)

		# sorted_list = sort_by_end_time(busylist)
		# if free_begin >= arrow.get(sorted_list[len(sorted_list)-1].end_datetime):
		# 	# All busy events end before the free period begins
		# 	return [ [self], [] ]

		sorted_list = sort_by_begin_time(busylist)
		# if free_end <= arrow.get(sorted_list[0].begin_datetime):
		# 	# All busy events begin after the free period ends
		# 	return [ [self], [] ]
		
		# There are busy events in the free period
		freetimes = [ ]
		busytimes = [ ]
		for busytime in sorted_list: # Uses the list sorted in ascending order by start time
			busy_begin = arrow.get(busytime.begin_datetime)
			busy_end = arrow.get(busytime.end_datetime)
			
			if busy_end <= free_begin:
				# Busy time is before the free period, continues until relevant busy time is found
				continue

			if busy_begin >= free_end:
				if freetimes == []:
					# There have been no busy times in the free period, and there won't be
					break
				# Busy time is after the free period, finish modifying free blocks of time
				if free_end > arrow.get(freetimes[len(freetimes)-1]["begin_datetime"]):
					# If the previous busy end time is before the free period end time,
					# then add the last block of free time
					freetimes[len(freetimes)-1]["end_datetime"] = free_end.isoformat()
					print("to {}(In for loop)\n".format(free_end.isoformat()))
				else:
					# If not, there should not be another block of free time. Removes
					# the previously initiated block
					del freetimes[len(freetimes)-1]
					print("...Last entry cancelled")
				break

			if freetimes == []:
				# First busy entry, Initializes the blocks of free time
				print("This is the first entry")
				if free_begin >= busy_begin and free_end <= busy_end:
					# Special case of when the free period is completely within a busy time
					return [ [],[busytime] ]
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
		if freetimes == []:
			# There have been no busy times in the free period
			return [ [self], [] ]
		if freetimes[len(freetimes)-1]["end_datetime"] == None:
			# Last busy time was within the free period, so there is a final block of
			# free time that ends at the end of the free period
			freetimes[len(freetimes)-1]["end_datetime"] = free_end.isoformat()
			print("to {} (After for loop)".format(free_end.isoformat()))
		
		# Convert the list of free time dicts into list of TimeSlots
		fts = freetimes
		freetimes = [ ]
		for ft in fts:
			freetimes.append(TimeSlot(['Free Time'], ft['begin_datetime'], ft['end_datetime']))

		return [freetimes, busytimes]


	def serialize(self):
		return {
			'summary': self.summary,
			'begin_datetime': self.begin_datetime,
			'end_datetime': self.end_datetime
		}


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
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.begin_datetime[:-6].replace('T','').replace('-','').replace(':','')))
	else:
		return sorted(timeslot_list, key=lambda timeslot: int(timeslot.begin_datetime[:-6].replace('T','').replace('-','').replace(':','')), reverse=True)


def serialize_list(timeslot_list):
	return [ts.serialize() for ts in timeslot_list]