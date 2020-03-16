# -*- coding: utf-8 -*-

from flask import Flask, request, Response, render_template, jsonify
from functions import generate_random_string, render, db, Users, Centers
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

@app.route('/', methods = ['GET'])
def index_route():
	return "Index"

@app.route('/twilio', methods = ['POST'])
def twilio_route():
	phone_number = request.form['From']
	message = request.form['Body']
	user = Users.query.filter_by(contact = phone_number).filter_by(platform = 'twilio').first()
	if user == None:
		new_user = Users(generate_random_string(10,20), 'twilio', phone_number)
		db.session.add(new_user)
		db.session.commit()
		user = Users.query.filter_by(contact = phone_number).filter_by(platform = 'twilio').first()
	response_message = render(user, message)
	xml = '<Response><Message>' + response_message + '</Message></Response>'
	return Response(xml, mimetype = 'text/xml')

@app.route('/api/centers', methods = ['GET'])
def get_centers_route():
	centers = Centers.query.all()
	return jsonify({'data': [ center.json() for center in centers ]})

@app.route('/api/centers/<center_id>', methods = ['GET'])
def get_center_route(center_id):
	center = Centers.query.filter_by(id = center_id).first()
	if center == None:
		return jsonify({'status':'error', 'message':'Coronavirus Screening Center with this ID does not exist.'})
	return jsonify({'status':'success','data':center.json()})

if __name__ == "__main__":
	app.run(debug=True, use_reloader=True)