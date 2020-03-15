import requests
from bs4 import BeautifulSoup
import random
from models import db, Users, Centers
import os
from dotenv import load_dotenv
import re

load_dotenv(verbose=True)

def generate_random_string(min_num, max_num):
	char_bank = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
	ret_string = ""
	for x in range(random.randint(min_num, max_num)):
		ret_string += char_bank[random.randint(0, len(char_bank) - 1)]
	return ret_string

def geolocate(text):
	url = 'https://maps.googleapis.com/maps/api/geocode/json?address=' + text + '&key=' + os.getenv('GEOLOCATION_API_KEY')
	r = requests.get(url)
	data = r.json()
	if 'results' not in data:
		return None
	lat = data['results'][0]['geometry']['location']['lat']
	lng = data['results'][0]['geometry']['location']['lng']
	return {'lat' : lat, 'lng' : lng}

def search_for_zip_code(text):
	result = re.match('^\d{5}(?:[-\s]\d{4})?$', text)
	if result == False:
		return None
	return text

def search_for_directions(x_coord_1, y_coord_1, x_coord_2, y_coord_2, mode):
	directions = []
	coords_one = str(y_coord_1) + ','  + str(x_coord_1)
	coords_two = str(y_coord_2) + ','  + str(x_coord_2)

	url = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + coords_one + '&destination=' + coords_two + '&key=' + os.getenv('GEOLOCATION_API_KEY') + '&mode=' + mode
	r = requests.get(url)
	data = r.json()
	if "routes" not in data:
		return None
	steps = data['routes'][0]['legs'][0]['steps']
	for step in steps:
		soup = BeautifulSoup(step['html_instructions'])
		if mode == "transit":
			if 'transit_details' in step:
				directions.append("Take " + step['transit_details']['line']['short_name'] + " " + soup.get_text())
			else:
				directions.append(soup.get_text())
		else:		
			directions.append(soup.get_text())
	direction_text = ". ".join(directions)
	return direction_text

def translate(user, text):
	#if the user language is English speaking, simply return the text
	if user.language == "en":
		return text
	#if the user language is not known, then simply return the text
	if user.language == "unkn":
		return text
	#Otherwise, get the text 
	url = "https://translation.googleapis.com/language/translate/v2?key=" + os.getenv('TRANSLATION_API_KEY')
	r = requests.post(url, data = {'q' : text, 'source' : 'en','target' : user.language, 'format' : 'text'})
	data = r.json()
	if 'data' not in data:
		return text
	return data['data']['translations'][0]['translatedText']

def search_for_address(text):
	text = text.split(" ")
	address_array = []
	address_endings = ['alley','aly','annex','anex','anx','arcade',
		'arc','avenue','ave','bayou','byu','boulevard','blvd','branch','br','bridge','brg','brook',
		'brk','center','ctr','circle','cir','court','ct','drive','dr','expressway','expy','fld','flts',
		'frge','freeway','fwy','gtwy','highway','hwy','lane','ln','lodge','ldg','manor','mnr','meadow',
		'mdw','mdws','park','pkwy','parkway','place','pl','plaza','plz','road','rd','route','rte','skyway',
		'skwy','street','st','terrace','ter','trafficway','trfy','way']
	address_started = 0
	list_index = len(text)
	while list_index >= 1:
		list_index -= 1
		word = text[list_index]
		if address_started == 0:
			if word.lower() in address_endings:
				address_started = 1
				address_array.append(word)
		elif address_started == 1:
			address_array.append(word)
			if word.isdigit():
				address_started = 2
		elif address_started == 2:
			pass
		else:
			pass

	if len(address_array) == 0:
		return False
	address_array.reverse()
	return "+".join(address_array)


def return_language_message(user, text):
	user.state += 1
	db.session.commit()
	return translate(user, 
		"If you speak English, text the number 1. \
		If you speak Spanish, text the number 2. \
		If you speak Chinese, text the number 3. \
		If you speak Vietnamese, text the number 4. \
		If you speak French, text the number 5. \
		If you speak Arabic, text the number 6. ")

def return_address_message(user, text):
	language_bank = {
		'1' : 'en',
		'2' : 'es',
		'3' : 'zh-CN',
		'4' : 'vi',
		'5' : '',
		'6' : ''
	}

	if text not in language_bank.keys():
		return translate(user, "Sorry. I did not understand your response. \
			If you speak English, text the number 1. \
			If you speak Spanish, text the number 2. \
			If you speak Chinese, text the number 3. \
			If you speak Vietnamese, text the number 4. \
			If you speak French, text the number 5. \
			If you speak Arabic, text the number 6. ")
	user.language = language_bank[text]
	user.state += 1
	db.session.commit()

	return translate(user, "Hi. This chatbot is here to help you find the nearest coronavirus testing center. \
		What is your address?")

def return_zip_code_message(user, text):
	text = text.replace(".","").replace(",","").replace("?","").replace("!","").replace(";","")
	address = search_for_address(text)
	if address == False:
		return translate(user, "Invalid address. Please send a valid street address.")
	user.address = address
	user.state += 1
	db.session.commit()
	return translate(user, "What is your zip code?")

def return_location_message(user, text):
	zip_code = search_for_zip_code(text)
	if zip_code == False:
		return translate(user, "Invalid zip code. Please send a valid zip code.")
	user.zip_code = zip_code
	search_address = "{}+{}".format(user.address, user.zip_code)
	coords = geolocate(search_address)

	if coords == None: 
		user.state == 6
		db.session.commit()
		return translate(user, "Something went wrong. Please try again later.")

	user.lat = coords['lat']
	user.lng = coords['lng']

	user.state += 1
	db.session.commit()

	max_distance = 10000000000000
	closest_center = None
	testing_centers = Centers.query.all()
	for testing_center in testing_centers:
		if testing_center.haversine(user.lat, user.lng) <= max_distance:
			max_distance = testing_center.haversine(user.lat, user.lng)
			closest_center = testing_center
	
	if closest_center == None: 
		return translate(user, "Something went wrong. Please try again later.")

	return translate(user, "The nearest place for coronavirus testing is {} at {}, {}, {}. Would you like directions?\
		Text the number 1 for yes. Otherwise, text the number 2 for no.")

def return_mode_message(user, text):
	if text == "1":
		user.state += 1
		db.session.commit()
		return translate(user, "How would you like to get there? Text the number 1 if you want to get there by car. \
			Text the number 2 if you want to get there by public transit.")
	elif text == "2":
		user.state = 2
		db.session.commit()
		return translate(user, "Thank you for using this chatbot. Please know that you should only go get tested if you are showing the symptoms of the coronavirus. \
			If you want to search again, please text a valid street address.")
	return translate(user, "I'm sorry. I did not understand your response. If you want directions, text the number 1. Otherwise, text the number 2.")

def return_directions_message(user, text):
	transit_mode_dict = {'1':'driving','2':'transit'}
	if text not in transit_mode_dict.keys():
		return translate(user, "I'm sorry. I did not understand your response. If you want to get there by car, text the number 1. \
			If you want to get there by public transit, text the number 2.")
	testing_centers = Centers.query.all()
	max_distance = 10000000000000
	closest_center = None
	for testing_center in testing_centers:
		if testing_center.haversine(user.lat, user.lng) <= max_distance:
			max_distance = testing_center.haversine(user.lat, user.lng)
			closest_center = testing_center
	
	if closest_center == None: 
		return translate(user, "Something went wrong. Please try again later.")

	directions = search_for_directions(user.lng, user.lat, closest_center.lng, closest_center.lat, transit_mode_dict[text]).replace("Destination",". Destination")
	user.state = 2
	db.session.commit()
	return translate(user, "Directions to {}: {}. Thank you for using this chatbot. Please know that you should only go get tested if you are showing the symptoms of the coronavirus \
		If you want to search again, please text a valid street address.".format(closest_center.name, directions))


def render(user, text):
	if user.state == 0:
		return return_language_message(user, text)
	elif user.state == 1:
		return return_address_message(user, text)
	elif user.state == 2:
		return return_zip_code_message(user, text)
	elif user.state == 3:
		return return_location_message(user, text)
	elif user.state == 4:
		return return_mode_message(user, text)
	elif user.state == 5:
		return return_directions_message(user, text)
