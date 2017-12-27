from app import app
from flask import request, jsonify

import models

@app.route('/encounters/<int:patient_id>', methods = ['GET', 'POST'])
def encounter(patient_id):
    if request.method == 'GET':
        result = models.get_encounters(patient_id)
        if result is None:
            return {'status': 400, 'message': 'Clinical data for patient {} not found'.format(patient_id)}
        mediatorResponse = jsonify(result)
        mediatorResponse.headers["Content-Type"] = 'application/json+openhim'
        return mediatorResponse
    else:
        data = request.get_json()
        data['patient_id'] = patient_id
        result = models.save_encounter(data)
        if result is None:
            return {'status': 400, 'message': 'Encounter not inserted. Insufficient data.'}
        mediatorResponse = jsonify(result)
        mediatorResponse.headers["Content-Type"] = 'application/json+openhim'
        return mediatorResponse

@app.route('/encounters/', methods = ['POST'])
def save_encounter():
    data = request.get_json()
    encounter_id = models.save_encounter(data)
    if encounter_id is None:
        return {'status': 400, 'message': 'Insufficient Data'}
    mediatorResponse = jsonify(encounter_id)
    mediatorResponse.headers["Content-Type"] = 'application/json+openhim'
    return mediatorResponse, 201

