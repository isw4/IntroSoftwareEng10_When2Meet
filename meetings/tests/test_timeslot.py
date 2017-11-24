from timeslot import TimeSlot, sort_by_begin_time, sort_by_end_time
from random import shuffle
import arrow, timeslot

#############################################################################
#
# Testing Merge
#
#############################################################################

def test_merge_unable():
	# A before B
	A = TimeSlot('A', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T10:01:00+00:00', '2013-05-12T11:00:00+00:00')
	assert A.merge(B) == None and B.merge(A) == None

	# A after B
	A = TimeSlot('A', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T08:00:00+00:00', '2013-05-12T08:59:00+00:00')
	assert A.merge(B) == None and B.merge(A) == None


def test_merge_able():
	# A fits just before B
	A = TimeSlot('A', '2013-05-12T08:00:00+00:00', '2013-05-12T09:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T09:00:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T09:00:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T10:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))

	# A fits just after B
	A = TimeSlot('A', '2013-05-12T10:00:00+00:00', '2013-05-12T11:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T10:00:00+00:00', 'end_datetime':'2013-05-12T11:00:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T11:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T10:00:00+00:00', 'end_datetime':'2013-05-12T11:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T11:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))

	# A front overlaps B
	A = TimeSlot('A', '2013-05-12T08:00:00+00:00', '2013-05-12T09:30:00+00:00')
	B = TimeSlot('B', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T09:30:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T09:30:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T10:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))
	
	# A back overlaps B
	A = TimeSlot('A', '2013-05-12T09:30:00+00:00', '2013-05-12T12:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T09:30:00+00:00', 'end_datetime':'2013-05-12T12:00:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T12:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T09:30:00+00:00', 'end_datetime':'2013-05-12T12:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T12:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))
	
	# A same as B
	A = TimeSlot('A', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T09:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))

	# A completely overlaps B
	A = TimeSlot('A', '2013-05-12T08:00:00+00:00', '2013-05-12T12:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T08:00:00+00:00', '2013-05-12T10:00:00+00:00')
	ansAB = TimeSlot([ {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T12:00:00+00:00'},
					   {'summary':'B', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T12:00:00+00:00')
	ansBA = TimeSlot([ {'summary':'B', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T10:00:00+00:00'},
					   {'summary':'A', 'begin_datetime':'2013-05-12T08:00:00+00:00', 'end_datetime':'2013-05-12T12:00:00+00:00'}],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T12:00:00+00:00')
	assert ansAB.equals(A.merge(B)) and ansBA.equals(B.merge(A))


#############################################################################
#
# Testing Sort
#
#############################################################################


def test_sort():
	A = TimeSlot('A', '2017-11-12T09:00:00+00:00', '2017-11-12T17:00:00+00:00')
	B = TimeSlot('B', '2017-11-13T09:00:00+00:00', '2017-11-13T17:00:00+00:00')
	C = TimeSlot('C', '2017-11-14T00:00:00-08:00', '2017-11-15T00:00:00-08:00')
	D = TimeSlot('D', '2017-11-15T09:00:00+00:00', '2017-11-15T17:00:00+00:00')
	E = TimeSlot('E', '2017-11-15T21:00:00-08:00', '2017-11-16T10:00:00-08:00')
	F = TimeSlot('F', '2017-11-17T00:00:00-08:00', '2017-11-19T00:00:00-08:00')
	unsorted = [A,B,C,D,E,F]
	shuffle(unsorted)

	# Begin time, ascending
	ans = [A,B,C,D,E,F]
	sort = sort_by_begin_time(unsorted, timeslot.ASCENDING)
	assert len(sort) == len(ans)
	for i in range(0,len(ans)):
		assert ans[i].equals(sort[i])

	# End time, descending
	ans = [F,E,D,C,B,A]
	sort = sort_by_end_time(unsorted, timeslot.DESCENDING)
	assert len(sort) == len(ans)
	for i in range(0,len(ans)):
		assert ans[i].equals(sort[i])


#############################################################################
#
# Testing Finding Free and Busy Times
#
#############################################################################

def test_find_freebusy():
	A = TimeSlot('A', '2013-05-12T08:00:00+00:00', '2013-05-12T09:00:00+00:00')
	B = TimeSlot('B', '2013-05-12T10:00:00+00:00', '2013-05-12T11:00:00+00:00')
	C = TimeSlot('C', '2013-05-12T12:00:00+00:00', '2013-05-12T13:00:00+00:00')
	D = TimeSlot('D', '2013-05-12T14:00:00+00:00', '2013-05-12T15:00:00+00:00')
	E = TimeSlot('E', '2013-05-12T16:00:00+00:00', '2013-05-12T17:00:00+00:00')
	F = TimeSlot('F', '2013-05-14T16:00:00+00:00', '2013-05-14T17:00:00+00:00')

	"""
	All busy times after free period:
	time 	free 	busy 	res
	05:00			
	06:00	[]				[]
	07:00	[]				[]
	08:00			[]
	09:00					
	10:00			[]
	"""
	free = TimeSlot('Free Period', '2013-05-12T06:00:00+00:00', '2013-05-12T08:00:00+00:00')
	ansF = [ TimeSlot('Free Period', '2013-05-12T06:00:00+00:00', '2013-05-12T08:00:00+00:00') ]
	ansB = [ ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1]) and free.equals(ansF[0])

	"""
	All busy times before the free period:
	time 	free 	busy 	res
	16:00			[]last
	17:00	[]				[]
	18:00	[]				[]
	19:00			
	"""
	free = TimeSlot('Free Period', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00')
	ansF = [ TimeSlot('Free Period', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00') ]
	ansB = [ ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1]) and free.equals(ansF[0])
	
	"""
	No busy times in free period:
	time 	free 	busy 	res
	12:00			[]
	13:00	[]				[]
	14:00			[]		
	15:00			
	"""
	free = TimeSlot('Free Period', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00')
	ansF = [ TimeSlot('Free Period', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00') ]
	ansB = [ ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1]) and free.equals(ansF[0])

	"""
	All busy times in free period
	time 	free 	busy 	res
	06:00
	07:00	[]				[]
	08:00	[]		[]
	09:00	[]				[]
	10:00	[]		[]		
	11:00	[]				[]
	12:00	[]		[]
	13:00	[]				[]
	14:00	[]		[]
	15:00	[]				[]
	16:00	[]		[]
	17:00	[]				[]
	18:00	[]				[]
	19:00					
	"""
	print("All busy times within free period:")
	free = TimeSlot('Free Period', '2013-05-12T07:00:00+00:00', '2013-05-12T19:00:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T07:00:00+00:00', '2013-05-12T08:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T15:00:00+00:00', '2013-05-12T16:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00') ]
	ansB = [ A, B, C, D, E ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])


	"""
	One busy time takes up whole free period
	time 	free 	busy 	res
	08:00			[]
	08:15	[]		[]
	08:30	[]		[]
	08:45			[]
	09:00					
	09:15	
	"""
	free = TimeSlot('Free Period', '2013-05-12T08:15:00+00:00', '2013-05-12T08:45:00+00:00')
	ansF = [ ]
	ansB = [ A ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	assert ansB[0].equals(res[1][0])

	# Other cases
	"""
	time 	free 	busy 	res
	09:30					
	10:00	[]		[]
	10:30	[]		[]
	11:00	[]				[]
	11:30	[]				[]
	12:00	[]		[]
	12:30	[]		[]
	"""
	free = TimeSlot('Free Period', '2013-05-12T10:00:00+00:00', '2013-05-12T19:00:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T15:00:00+00:00', '2013-05-12T16:00:00+00:00'),
		 	 TimeSlot('Free Time', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00') ]
	ansB = [ B, C, D, E]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])

	"""
	time 	free 	busy 	res
	09:30					
	10:00			[]
	10:30	[]		[]
	11:00	[]				[]
	11:30	[]				[]
	12:00	[]		[]
	12:30	[]		[]
	"""
	free = TimeSlot('Free Period', '2013-05-12T10:30:00+00:00', '2013-05-12T19:00:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T15:00:00+00:00', '2013-05-12T16:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00') ]
	ansB = [ B, C, D, E]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])

	"""
	time 	free 	busy 	res
	09:30					
	10:00			[]
	10:30			[]
	11:00	[]				[]
	11:30	[]				[]
	12:00	[]		[]
	12:30	[]		[]
	"""
	free = TimeSlot('Free Period', '2013-05-12T11:00:00+00:00', '2013-05-12T19:00:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T15:00:00+00:00', '2013-05-12T16:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T17:00:00+00:00', '2013-05-12T19:00:00+00:00') ]
	ansB = [ C, D, E ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])

	"""
	time 	free 	busy 	res
	13:30	[]				[]
	14:00	[]		[]
	14:30			[]
	15:00					
	15:30
	16:00			[]
	16:30			[]last
	"""
	free = TimeSlot('Free Period', '2013-05-12T07:00:00+00:00', '2013-05-12T14:30:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T07:00:00+00:00', '2013-05-12T08:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00') ]
	ansB = [ A, B, C, D ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])


	"""
	time 	free 	busy 	res
	13:30	[]				[]
	14:00	[]		[]
	14:30	[]		[]
	15:00					
	15:30
	16:00			[]
	16:30			[]last
	"""
	print("Some busy ends at same time as the end of the free period")
	free = TimeSlot('Free Period', '2013-05-12T07:00:00+00:00', '2013-05-12T15:00:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T07:00:00+00:00', '2013-05-12T08:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00') ]
	ansB = [ A, B, C, D ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])

	"""
	time 	free 	busy 	res
	13:30	[]				[]
	14:00	[]		[]
	14:30	[]		[]
	15:00	[]				[]
	15:30
	16:00			[]
	16:30			[]last
	"""
	free = TimeSlot('Free Period', '2013-05-12T07:00:00+00:00', '2013-05-12T15:30:00+00:00')
	ansF = [ TimeSlot('Free Time', '2013-05-12T07:00:00+00:00', '2013-05-12T08:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T09:00:00+00:00', '2013-05-12T10:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T11:00:00+00:00', '2013-05-12T12:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T13:00:00+00:00', '2013-05-12T14:00:00+00:00'),
			 TimeSlot('Free Time', '2013-05-12T15:00:00+00:00', '2013-05-12T15:30:00+00:00') ]
	ansB = [ A, B, C, D ]
	res = free.find_freebusy_from([E,C,B,A,D])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])


def test_merge_freebusy():
	# Merge Case
	A = TimeSlot('All Day',   '2013-05-12T00:00:00+00:00', '2013-05-13T00:00:00+00:00')
	B = TimeSlot('Lunch',     '2013-05-12T12:00:00+00:00', '2013-05-12T13:00:00+00:00')
	C = TimeSlot('Dinner',    '2013-05-12T18:00:00+00:00', '2013-05-12T19:00:00+00:00')
	D = TimeSlot('Work Mtg',  '2013-05-12T14:00:00+00:00', '2013-05-12T15:00:00+00:00')
	E = TimeSlot('Work',      '2013-05-12T08:00:00+00:00', '2013-05-12T17:00:00+00:00')
	F = TimeSlot('Night Jog', '2013-05-12T20:00:00+00:00', '2013-05-12T21:00:00+00:00')

	free = TimeSlot('Free Period', '2013-05-12T12:00:00+00:00', '2013-05-12T22:00:00+00:00')
	ansF = [TimeSlot('Free Time', '2013-05-12T17:00:00+00:00', '2013-05-12T18:00:00+00:00'),
			TimeSlot('Free Time', '2013-05-12T19:00:00+00:00', '2013-05-12T20:00:00+00:00'),
			TimeSlot('Free Time', '2013-05-12T21:00:00+00:00', '2013-05-12T22:00:00+00:00')]
	ansB = [
			TimeSlot([ {'summary': 'Work', 'begin_datetime': '2013-05-12T08:00:00+00:00', 'end_datetime': '2013-05-12T17:00:00+00:00'},
					   {'summary': 'Lunch', 'begin_datetime': '2013-05-12T12:00:00+00:00', 'end_datetime': '2013-05-12T13:00:00+00:00'},
					   {'summary': 'Work Mtg', 'begin_datetime': '2013-05-12T14:00:00+00:00', 'end_datetime': '2013-05-12T15:00:00+00:00'} ],
					   '2013-05-12T08:00:00+00:00', '2013-05-12T17:00:00+00:00'),
			TimeSlot('Dinner', '2013-05-12T18:00:00+00:00', '2013-05-12T19:00:00+00:00'),
			TimeSlot('Night Jog', '2013-05-12T20:00:00+00:00', '2013-05-12T21:00:00+00:00')
			]
	res = free.find_freebusy_from([E,C,B,D,F])
	assert len(ansF) == len(res[0]) and len(ansB) == len(res[1])
	for i in range(0,len(ansF)):
		assert ansF[i].equals(res[0][i])
	for i in range(0,len(ansB)):
		assert ansB[i].equals(res[1][i])