import datetime
import requests

from utils.config import *

def get_encounters(patient_id):
    # validate user
    orchestration_results = []
    patient_object, patient_orchestration, status_code = create_orchestration('http://default-cr.cs300ohie.net', 
                                                                 '/patient/{}'.format(patient_id), 
                                                                 'Get Patient Information', 
                                                                 'GET')
    orchestration_results.append(patient_orchestration)

    encounter_ids, encounter_id_orchestration, status_code = create_orchestration('http://source-shr.cs300ohie.net',
                                                                     '/encounters/patient/{}'.format(patient_id),
                                                                     'Get Encounter Ids',
                                                                     'GET')
    orchestration_results.append(encounter_id_orchestration)

    encounters = []
    for encounter_id in encounter_ids:
        encounter_object, encounter_orchestration, status_code = create_orchestration('http://source-shr.cs300ohie.net',
                                                                         '/encounters/{}'.format(encounter_id),
                                                                         'Get Encounters',
                                                                         'GET')
        orchestration_results.append(encounter_orchestration)
        providers = []  
        for provider in encounter_object['providers']:
            provider_info, provider_orchestration, status_code = create_orchestration('http://default-hwr.cs300ohie.net',
                                                                         '/provider/{}'.format(provider['provider_id']),
                                                                         'Get Provider',
                                                                         'GET')
            orchestration_results.append(provider_orchestration)
            provider['attributes'] = provider_info['attributes']
            provider['identifier'] = provider_info['identifier']
            provider['name'] = provider_info['name']
            providers.append(provider_info)

        location_info, location_orchestration, status_code = create_orchestration('http://default-fr.cs300ohie.net',
                                                                     '/location/{}'.format(encounter_object['location_id']),
                                                                     'Get Location',
                                                                     'GET')
        orchestration_results.append(location_orchestration)
        
        encounter_object['location_name'] = location_info['name']
        encounters.append(encounter_object)

    properties = create_properties_object(patient_object, encounters)
    patient_object['encounters'] = encounters
    response = create_response_object(status_code, patient_object)
    return create_openhim_response_object(response, orchestration_results, properties)
    

def save_encounter(data):
    orchestration_results = []

    # validate client data and enrich record
    patient_object, patient_orchestration, status_code = create_orchestration('http://default-cr.cs300ohie.net', 
                                                                 '/patient/{}'.format(data['patient_id']), 
                                                                 'Validate Patient Information', 
                                                                 'GET')
    orchestration_results.append(patient_orchestration)
    # validate all provider data and enrich record
    for provider in data['providers']:
        provider_info, provider_orchestration, status_code = create_orchestration('http://default-hwr.cs300ohie.net',
                                                                    '/provider/{}'.format(provider['provider_id']),
                                                                    'Validate Provider',
                                                                    'GET')
    orchestration_results.append(provider_orchestration)    
    # validate location data and enrich record
    location_info, location_orchestration, status_code = create_orchestration('http://default-fr.cs300ohie.net',
                                                                 '/location/{}'.format(data['location_id']),
                                                                 'Validate Location',
                                                                 'GET')
    orchestration_results.append(location_orchestration)

    encounter_id, orchestration, status_code = create_orchestration('http://source-shr.cs300ohie.net',
                                                                    '/encounters',
                                                                    'Create Encounter',
                                                                    'POST',
                                                                    headers={'Content-Type': 'application/json'},
                                                                    request_body=data)
    orchestration_results.append(orchestration)

    response = create_response_object(status_code, encounter_id)
    properties = {
        'patient id': data['patient_id'],
        'encounter id': encounter_id
    }
    return create_openhim_response_object(response, orchestration_results, properties)


def create_openhim_response_object(response, orchestrations, properties):
    return {
        'x-mediator-urn': urn,
        'status': 'Successful',
        'response': response,
        'orchestrations': orchestrations,
        'properties': properties
    }

def create_orchestration(domain, path, name, method, headers=None, params='', request_body=None):
    orchestration_url = domain + path + params

    response = requests.request(method ,orchestration_url, headers = headers, json = request_body if request_body else None)

    context_object = response.json()

    if context_object is None:
        context_object = {'message': 'Error at {} {}'.format(method, orchestration_url),'status': response.status_code}

    orchestration_result = {
        'name': name,
        'request': {
            'path': path,
            'headers': headers,
            'querystring': params,
            'body': request_body,
            'method': method,
            'timestamp': str(int(datetime.datetime.now().timestamp()*100))
        },
        'response': {
            'status': response.status_code,
            'body': json.dumps(context_object),
            'timestamp': str(int(datetime.datetime.now().timestamp()*100))
        }
    }
    return context_object, orchestration_result, response.status_code

def create_response_object(status_code, body):
    return {
        'status': status_code,
        'headers': {
            'content-type': 'application/json'
        },
        'body': body,
        'timestamp': str(int(datetime.datetime.now().timestamp()*100))
    }

def create_properties_object(patient, encounters):
    properties = {
        'patient name': patient['family_name'] + patient['middle_name'],
        'city': patient['city'],
        'gender': patient['gender']
    }
    for i in range(len(encounters)):
        properties['Encounter {}'.format(i + 1)] = '{}, {}, {}'.format(encounters[i]['encounter_type_description'], 
                                                                        encounters[i]['location_name'], 
                                                                        encounters[i]['encounter_datetime'])
    return properties