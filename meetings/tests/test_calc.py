from calc import init_frees_by_date, merge_single_list, intersect_two_lists
from random import shuffle
from timeslot import TimeSlot
import timeslot


def test_init():
	begin_datetime = '2017-04-10T08:00:00-05:00'
	end_datetime = '2017-04-15T19:00:00-05:00'
	init = init_frees_by_date(begin_datetime, end_datetime)
	ans = [
		TimeSlot('2017-04-10T08:00:00-05:00', '2017-04-10T19:00:00-05:00'),
		TimeSlot('2017-04-11T08:00:00-05:00', '2017-04-11T19:00:00-05:00'),
		TimeSlot('2017-04-12T08:00:00-05:00', '2017-04-12T19:00:00-05:00'),
		TimeSlot('2017-04-13T08:00:00-05:00', '2017-04-13T19:00:00-05:00'),
		TimeSlot('2017-04-14T08:00:00-05:00', '2017-04-14T19:00:00-05:00'),
		TimeSlot('2017-04-15T08:00:00-05:00', '2017-04-15T19:00:00-05:00'),
		]
	assert len(init) == len(ans)
	for i in range(0, len(init)):
		assert init[i].equals(ans[i])


def test_mergelist():
	unmerged = [
		TimeSlot('2017-04-10T06:00:00+00:00', '2017-04-10T07:00:00+00:00'),
		TimeSlot('2017-04-10T08:00:00+00:00', '2017-04-10T08:30:00+00:00'),
		TimeSlot('2017-04-10T08:30:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('2017-04-10T08:30:00+00:00', '2017-04-10T09:00:00+00:00'),
		TimeSlot('2017-04-10T08:45:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('2017-04-10T15:00:00+00:00', '2017-04-10T16:00:00+00:00'),
		TimeSlot('2017-04-10T15:30:00+00:00', '2017-04-10T16:00:00+00:00'),
		TimeSlot('2017-04-10T15:15:00+00:00', '2017-04-10T18:00:00+00:00'),
		TimeSlot('2017-04-10T22:00:00+00:00', '2017-04-10T23:00:00+00:00')
		]
	ans = [
		TimeSlot('2017-04-10T06:00:00+00:00', '2017-04-10T07:00:00+00:00'),
		TimeSlot('2017-04-10T08:00:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('2017-04-10T15:00:00+00:00', '2017-04-10T18:00:00+00:00'),
		TimeSlot('2017-04-10T22:00:00+00:00', '2017-04-10T23:00:00+00:00')
		]
	shuffle(unmerged)
	merged = merge_single_list(unmerged)
	assert len(merged) == len(ans)
	for i in range(0, len(merged)):
		assert merged[i].equals(ans[i])


def test_intersectlist():
	list_a = [
		TimeSlot('2017-04-10T06:00:00+00:00', '2017-04-10T07:00:00+00:00'),
		TimeSlot('2017-04-10T08:30:00+00:00', '2017-04-10T09:00:00+00:00'),
		TimeSlot('2017-04-10T10:30:00+00:00', '2017-04-10T11:30:00+00:00'),
		TimeSlot('2017-04-10T15:00:00+00:00', '2017-04-10T16:00:00+00:00')
		]

	list_b = [
		TimeSlot('2017-04-10T08:30:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('2017-04-10T14:00:00+00:00', '2017-04-10T15:15:00+00:00'),
		TimeSlot('2017-04-10T15:30:00+00:00', '2017-04-10T16:00:00+00:00'),
		TimeSlot('2017-04-10T22:00:00+00:00', '2017-04-10T23:00:00+00:00')
		]

	ans = [
		TimeSlot('2017-04-10T08:30:00+00:00', '2017-04-10T09:00:00+00:00'),
		TimeSlot('2017-04-10T10:30:00+00:00', '2017-04-10T11:00:00+00:00'),
		TimeSlot('2017-04-10T15:00:00+00:00', '2017-04-10T15:15:00+00:00'),
		TimeSlot('2017-04-10T15:30:00+00:00', '2017-04-10T16:00:00+00:00'),
		]
	ab_intersect = intersect_two_lists(list_a, list_b)
	ab_intersect = timeslot.sort_by_begin_time(ab_intersect, timeslot.ASCENDING)
	assert len(ans) == len(ab_intersect)
	for i in range(0, len(ab_intersect)):
		assert ans[i].equals(ab_intersect[i])


test_mergelist()
test_init()
test_intersectlist()