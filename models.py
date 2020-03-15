from flask_sqlalchemy import SQLAlchemy
import random
from datetime import datetime
from math import radians, sin, cos, asin
db = SQLAlchemy()

class Users(db.Model):
	id = db.Column(db.String(255), primary_key = True)
	platform = db.Column(db.String(30))
	contact = db.Column(db.String(255))
	language = db.Column(db.String(5))
	address = db.Column(db.String(255))
	zip_code = db.Column(db.String(5))
	mode_of_transportation = db.Column(db.String(7))
	lat = db.Column(db.Float)
	lng = db.Column(db.Float)
	state = db.Column(db.Integer)

	def __init__(self, id, platform, contact):
		self.id = id
		self.platform = platform
		self.contact = contact
		self.language = "unkn"
		self.zip_code = "unkn"
		self.mode_of_transportation = "unkn"
		self.state = 0

class Searches(db.Model):
	id = db.Column(db.String(255), primary_key = True)
	user_id = db.Column(db.String(255))
	search_time = db.Column(db.DateTime)

	def __init__(self, user_id):
		self.id = id
		self.user_id = user_id
		self.search_time = datetime.now()


class Centers(db.Model):
	id = db.Column(db.String(255), primary_key = True)
	name = db.Column(db.String(255))
	address = db.Column(db.String(255))
	city = db.Column(db.String(50))
	state = db.Column(db.String(5))
	zip_code = db.Column(db.String(15))
	lat = db.Column(db.Float)
	lng = db.Column(db.Float)

	def __init__(self, id, name, address, city, state, zip_code, lat, lng):
		self.id = id
		self.name = name
		self.address = address
		self.city = city
		self.state = state
		self.zip_code = zip_code
		self.lat = lat
		self.lng = lng

	def haversine(self, lat2, lng2):
		lng1, lat1, lng2, lat2 = map(radians, [self.lng, self.lat, lng2, lat2])
		dlng = lng2 - lng1
		dlat = lat2 - lat1
		a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
		c = 2 * asin(sqrt(a))
		r = 6371 
		return c * r