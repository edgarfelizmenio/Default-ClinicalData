from app import app
from flask import request, jsonify

import models

@app.route('/encounters/<int:patient_id>')
def get_encounter(patient_id):
    encounters = models.get_encounters(patient_id)
    if encounters is None:
        return {'status': 400, 'message': 'Clinical data for patient {} not found'.format(patient_id)}
    mediatorResponse = jsonify(encounters)
    mediatorResponse.headers["Content-Type"] = 'application/json+openhim'
    return mediatorResponse

def post(self, patient_id):
    data = request.get_json()
    encounter_id = models.add_encounter(patient_id, data)
    if encounter_id is None:
        return {'status': 400, 'message': 'Insufficient Data'}
    return encounter_id, 201