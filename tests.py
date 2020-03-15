import requests


test1 = requests.post("http://localhost:5000/twilio", data = {
		'From' : '1234567890',
		'Body' : 'Corona'
	})
print(test1.text)