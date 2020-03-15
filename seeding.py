from app import app
from models import db, Centers
from functions import geolocate, generate_random_string

import csv

with app.app_context():
	with open("locations.csv","r", encoding = "utf-8") as file_to_read:
		csv_to_read = csv.reader(file_to_read)
		for row in csv_to_read:
			if row[0] != "Name":
				address = "{}+{}+{}+{}".format(row[1],row[2],row[3],row[4]).replace("+","")
				coords = geolocate(address)
				new_center = Centers(
					generate_random_string(20,50),
					row[0],
					row[1],
					row[2],
					row[3],
					row[4],
					coords['lat'],
					coords['lng']
				)
				db.session.add(new_center)
				db.session.commit()



print("finished")