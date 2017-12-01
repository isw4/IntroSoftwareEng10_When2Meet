import uuid
import pymongo
from bson.objectid import ObjectId
from timeslot import TimeSlot
import timeslot
import calc
import arrow

"""
Class to navigate the database collection
"""
class DatabaseNav:
	collection = None

	def __init__(self, collection):
		self.collection = collection

	def insert_mtg(self, begin_datetime, end_datetime, duration, emails, times, desc):
		"""
		Inserts a meeting into the database, and returns the meeting id string. This is only meant to initiate a new
		meeting. The meeting has the structure:

			_id: 			ObjectId, id of the meeting(provided by Mongo when inserting)
			begin_datetime:	str, iso-formatted datetime of the begin date and begin time to arrange the meeting
			end_datetime:	str, iso-formatted datetime of the end date and end time to arrange the meeting
			duration:		str, HH:mm time of how long the meeting is
			inviter:	list of dictionaries, containing:
				inv_id:		str, id of the inviter
				freetimes:	list of dictionaries, representing the free times of the inviter:
					begin_datetime: str, iso-formatted datetime
					end_datetime:	str, iso-formatted datetime
			invitees:	list of dictionaries, containing:
				inv_id:		str, invitee id
				email:		str, invitee email
				responded:	boolean, whether the invitee has responded (should all be False)
				freetimes:	list of dictionaries, representing the free times of the inviter:
					begin_datetime: str, iso-formatted datetime
					end_datetime:	str, iso-formatted datetime
			desc:		str, short description of the meeting

		Args:
			begin_datetime: str, iso-formatted datetime of the begin date and begin time to arrange the meeting
			end_datetime:	str, iso-formatted datetime of the end date and end time to arrange the meeting
			duration:		str, HH:mm time of how long the meeting is
			emails:			list of str, emails of all invitees
			times:			list of dictionaries,  containing the list of free times from the inviter
			desc:			str, short description of the meeting

		Returns:
			str, meeting id
		"""
		doc = { }
		doc['begin_datetime'] = begin_datetime
		doc['end_datetime'] = end_datetime
		doc['duration'] = duration
		doc['inviter'] = { 'inv_id': str(uuid.uuid4()).replace('-',''),
						   'freetimes': times }
		doc['invitees'] = [ ]
		for email in emails:
			temp = { }
			temp['inv_id'] = str(uuid.uuid4()).replace('-','')
			temp['email'] = email
			temp['responded'] = False
			temp['freetimes'] = []
			doc['invitees'].append(temp)
		doc['desc'] = desc
		
		result = self.collection.insert_one(doc)
		return str(result.inserted_id)


	def get_mtg_invites(self, mtg_id):
		""" Getting information to build links to check and respond to this meeting """
		result = self.collection.find_one({'_id': ObjectId(mtg_id)})
		invitees = [ ]
		for invitee in result['invitees']:
			invitees.append({
				'email': invitee['email'],
				'id': invitee['inv_id'],
				'responded': invitee['responded']
				})
		return {
				'mtg_id': str(result['_id']),
				'inviter_id': result['inviter']['inv_id'],
				'invitees': invitees,
				'desc': result['desc'],
				'timezone': arrow.get(result['begin_datetime']).format('ZZ')
				}


	def get_mtg_for_user(self, mtg_id, user_id):
		""" Getting information relevant for a user to respond to meeting """
		result = self.collection.find_one({'_id': ObjectId(mtg_id)})
		if result == None:
			# Invalid meeting id
			return None
		if user_id == result['inviter']:
			# Meeting inviter wants to check the status of the meeting
			return 'inviter'
		for invitee in result['invitees']:
			if user_id == invitee['inv_id']:
				# Invitee wants to respond to meeting
				res = {}
				res['desc'] = result['desc']
				res['begin_datetime'] = result['begin_datetime']
				res['end_datetime'] = result['end_datetime']
				res['duration'] = result['duration']
				return res
		# Invalid user id
		return None


	def get_inviter_data(self, mtg_id, user_id):
		result = self.collection.find_one({'_id': ObjectId(mtg_id)})
		if result == None:
			# Invalid meeting id
			return None
		if user_id == result['inviter']['inv_id']:
			# Valid inviter. Get all inviter and invitee free times
			# Encoding freetimes into TimeSlot objects to allow for calculations
			raw_freetimes = result['inviter']['freetimes']
			inviter_freetimes = []
			for raw_ft in raw_freetimes:
				inviter_freetimes.append(TimeSlot(raw_ft['begin_datetime'], raw_ft['end_datetime']))
			
			invitee_freetimes = []
			for invitee in result['invitees']:
				# Encoding invitees data
				if not invitee['responded']:
					# Ignores invitees that have not responded from the calculations
					print('{} did not respond, skipping...'.format(invitee['email']))
					continue
				raw_freetimes = invitee['freetimes']
				print('raw freetimes {}'.format(raw_freetimes))
				temp = []
				for raw_ft in raw_freetimes:
					temp.append(TimeSlot(raw_ft['begin_datetime'], raw_ft['end_datetime']))
				invitee_freetimes.append(temp)
			
			# Finding the intersection of all user freetimes
			curr_inter = inviter_freetimes
			print('Inviter freetimes: {}'.format(curr_inter))
			for each_invitee in invitee_freetimes:
				print('Invitee freetimes: {}'.format(each_invitee))
				curr_inter = calc.intersect_two_lists(curr_inter, each_invitee)
				print('Intersection: {}'.format(curr_inter))
			
			# Putting together data
			data = {}
			data['desc'] = result['desc']
			data['duration'] = result['duration']
			data['begin_datetime'] = result['begin_datetime']
			data['end_datetime'] = result['end_datetime']
			data['freetimes'] = timeslot.serialize_list(timeslot.sort_by_begin_time(curr_inter, timeslot.ASCENDING))
			data['invitees'] = []
			for invitee in result['invitees']:
				temp = {}
				temp['email'] = invitee['email']
				temp['responded'] = invitee['responded']
				data['invitees'].append(temp)
			return data
		# Invalid user id
		return None


	def get_invitee_data(self, mtg_id, user_id):
		result = self.collection.find_one({'_id': ObjectId(mtg_id)})
		if result == None:
			# Invalid meeting id
			return None
		
		for invitee in result['invitees']:
			if user_id == invitee['inv_id']:
				if invitee['responded']:
					return 'responded'
				else:
					data = {}
					data['desc'] = result['desc']
					data['begin_datetime'] = result['begin_datetime']
					data['end_datetime'] = result['end_datetime']
					data['duration'] = result['duration']
					return data
		# Invalid user id
		return None


	def set_invitee_freetimes(self, mtg_id, user_id, times):
		""" Sets the freetimes for an invitee """
		result = self.collection.find_one({'_id': ObjectId(mtg_id)})
		if result == None:
			# Invalid meeting id
			return None

		for i in range(0, len(result['invitees'])):
			if user_id == result['invitees'][i]['inv_id']:
				if result['invitees'][i]['responded']:
					return 'responded'
				else:
					updated = self.collection.update_one({'_id': ObjectId(mtg_id)}, {'$set': {'invitees.{}.freetimes'.format(i): times}})
					updated = self.collection.update_one({'_id': ObjectId(mtg_id)}, {'$set': {'invitees.{}.responded'.format(i): True}})
					return 'updated'
		# Invalid user id
		return None


	def delete_mtg(self, _id):
		"""
		Deletes a memo from the database

		Args:
			_id:	string, id number of the document in the collection

		Returns:
			True if a document was deleted
			False otherwise
		"""
		result = self.collection.delete_one({'_id': ObjectId(_id)})
		if result.deleted_count == 1:
			  return True
		else: return False