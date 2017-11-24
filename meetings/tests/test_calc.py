from calc import init_frees_by_date, merge_single_list
from random import shuffle
from timeslot import TimeSlot


def test_init():
	begin_datetime = '2017-04-10T08:00:00-05:00'
	end_datetime = '2017-04-15T19:00:00-05:00'
	init = init_frees_by_date(begin_datetime, end_datetime)
	ans = [
		TimeSlot('Free Time', '2017-04-10T08:00:00-05:00', '2017-04-10T19:00:00-05:00'),
		TimeSlot('Free Time', '2017-04-11T08:00:00-05:00', '2017-04-11T19:00:00-05:00'),
		TimeSlot('Free Time', '2017-04-12T08:00:00-05:00', '2017-04-12T19:00:00-05:00'),
		TimeSlot('Free Time', '2017-04-13T08:00:00-05:00', '2017-04-13T19:00:00-05:00'),
		TimeSlot('Free Time', '2017-04-14T08:00:00-05:00', '2017-04-14T19:00:00-05:00'),
		TimeSlot('Free Time', '2017-04-15T08:00:00-05:00', '2017-04-15T19:00:00-05:00'),
		]
	assert len(init) == len(ans)
	for i in range(0, len(init)):
		assert init[i].equals(ans[i])


def test_mergelist():
	unmerged = [
		TimeSlot('6 to 7',      '2017-04-10T06:00:00+00:00', '2017-04-10T07:00:00+00:00'),
		TimeSlot('8 to 8:30',   '2017-04-10T08:00:00+00:00', '2017-04-10T08:30:00+00:00'),
		TimeSlot('8:30 to 11',  '2017-04-10T08:30:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('8:30 to 9',   '2017-04-10T08:30:00+00:00', '2017-04-10T09:00:00+00:00'),
		TimeSlot('8:45 to 11',  '2017-04-10T08:45:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('15 to 16',    '2017-04-10T15:00:00+00:00', '2017-04-10T16:00:00+00:00'),
		TimeSlot('15:30 to 16', '2017-04-10T15:30:00+00:00', '2017-04-10T16:00:00+00:00'),
		TimeSlot('15:15 to 18', '2017-04-10T15:15:00+00:00', '2017-04-10T18:00:00+00:00'),
		TimeSlot('22 to 23',    '2017-04-10T22:00:00+00:00', '2017-04-10T23:00:00+00:00')
		]
	ans = [
		TimeSlot('6 to 7', '2017-04-10T06:00:00+00:00', '2017-04-10T07:00:00+00:00'),
		TimeSlot([{ 'summary':'8 to 8:30',  'begin_datetime':'2017-04-10T08:00:00+00:00', 'end_datetime':'2017-04-10T08:30:00+00:00' },
				  { 'summary':'8:30 to 11', 'begin_datetime':'2017-04-10T08:30:00+00:00', 'end_datetime':'2017-04-10T11:00:00+00:00' },
				  { 'summary':'8:30 to 9',  'begin_datetime':'2017-04-10T08:30:00+00:00', 'end_datetime':'2017-04-10T09:00:00+00:00' },
				  { 'summary':'8:45 to 11', 'begin_datetime':'2017-04-10T08:45:00+00:00', 'end_datetime':'2017-04-10T11:00:00+00:00' }],
				  '2017-04-10T08:00:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot([{ 'summary':'15 to 16',    'begin_datetime':'2017-04-10T15:00:00+00:00', 'end_datetime':'2017-04-10T16:00:00+00:00' },
				  { 'summary':'15:15 to 18', 'begin_datetime':'2017-04-10T15:15:00+00:00', 'end_datetime':'2017-04-10T18:00:00+00:00' },
				  { 'summary':'15:30 to 16', 'begin_datetime':'2017-04-10T15:30:00+00:00', 'end_datetime':'2017-04-10T16:00:00+00:00' }],
				  '2017-04-10T15:00:00+00:00', '2017-04-10T18:00:00+00:00'),
		TimeSlot('22 to 23', '2017-04-10T22:00:00+00:00', '2017-04-10T23:00:00+00:00')
		]
	shuffle(unmerged)
	merged = merge_single_list(unmerged)
	assert len(merged) == len(ans)
	for i in range(0, len(merged)):
		assert merged[i].equals(ans[i])