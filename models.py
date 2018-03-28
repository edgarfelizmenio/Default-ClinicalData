import datetime
import concurrent.futures
import requests

from utils.config import *
import config

def get_encounters(patient_id):
    # validate user
    orchestration_results = []
    patient_object, patient_orchestration, status_code = create_orchestration(cr_url, 
                                                                 '/patient/{}'.format(patient_id), 
                                                                 'Get Patient Information', 
                                                                 'GET')
    orchestration_results.append(patient_orchestration)

    encounter_ids, encounter_id_orchestration, status_code = create_orchestration(shr_url,
                                                                     '/encounters/patient/{}'.format(patient_id),
                                                                     'Get Encounter Ids',
                                                                     'GET')
    orchestration_results.append(encounter_id_orchestration)

    encounters = []
    for encounter_id in encounter_ids:
        encounter_object, encounter_orchestration, status_code = create_orchestration(shr_url,
                                                                         '/encounters/{}'.format(encounter_id),
                                                                         'Get Encounters',
                                                                         'GET')
        orchestration_results.append(encounter_orchestration)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            provider_futures = []
            for provider in encounter_object['providers']:
                provider_future = executor.submit(create_orchestration, 
                                                  hwr_url,
                                                  '/provider/{}'.format(provider['provider_id']),
                                                  'Get Provider',
                                                  'GET')
                provider_futures.append(provider_future)
            location_future = executor.submit(create_orchestration, 
                                              fr_url,
                                              '/location/{}'.format(encounter_object['location_id']),
                                              'Get Location',
                                              'GET')

            for i in range(len(encounter_object['providers'])):
                provider_info, provider_orchestration, status_code = provider_futures[i].result()
                provider = encounter_object['providers'][i]
                provider['attributes'] = provider_info['attributes']
                provider['identifier'] = provider_info['identifier']
                provider['name'] = provider_info['name']
                orchestration_results.append(provider_orchestration)
            location_info, location_orchestration, status_code = location_future.result()
            encounter_object['location_name'] = location_info['name']
            orchestration_results.append(location_orchestration)

        encounters.append(encounter_object)

    properties = create_properties_object(patient_object, encounters)
    patient_object['encounters'] = encounters
    response = create_response_object(status_code, patient_object)
    return create_openhim_response_object(response, orchestration_results, properties)

def get_encounter(encounter_id):
    orchestration_results = []

    encounter_object, encounter_orchestration, status_code = create_orchestration(shr_url,
                                                                     '/encounters/{}'.format(encounter_id),
                                                                     'Get Encounters',
                                                                     'GET')
    orchestration_results.append(encounter_orchestration)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # validate patient
        cr_future = executor.submit(create_orchestration, 
                                    cr_url, 
                                    '/patient/{}'.format(encounter_object['patient_id']), 
                                    'Validate Patient Information', 
                                    'GET')
        # validate providers
        provider_futures = []
        for provider in encounter_object['providers']:
            provider_future = executor.submit(create_orchestration, 
                            hwr_url,
                            '/provider/{}'.format(provider['provider_id']),
                            'Validate Provider',
                            'GET')
            provider_futures.append(provider_future)
        # validate facility
        facility_future = executor.submit(create_orchestration,
                                          fr_url,
                                          '/location/{}'.format(encounter_object['location_id']),
                                          'Validate Location',
                                          'GET')

        patient_info, patient_orchestration, patient_status_code = cr_future.result()
        encounter_object['patient_name'] = '{} {}'.format(patient_info['given_name'], patient_info['family_name'])
        encounter_object['gender'] = patient_info['gender']
        encounter_object['city'] = patient_info['city']
        encounter_object['province'] = patient_info['province']
        encounter_object['country'] = patient_info['country']
        orchestration_results.append(patient_orchestration)

        for i in range(len(encounter_object['providers'])):
            provider_info, provider_orchestration, provider_status_code = provider_futures[i].result()
            provider = encounter_object['providers'][i]
            provider['attributes'] = provider_info['attributes']
            provider['identifier'] = provider_info['identifier']
            provider['name'] = provider_info['name']
            orchestration_results.append(provider_orchestration)
        
        facility_info, facility_orchestration, facility_status_code = facility_future.result()
        encounter_object['location_name'] = facility_info['name']
        orchestration_results.append(facility_orchestration)

    properties = {
        'Encounter': 'id: {}, Patient id: {}, {}, {}, {}'.format(
            encounter_object['encounter_id'], 
            encounter_object['patient_id'],
            encounter_object['encounter_type_description'],
            encounter_object['location_name'],
            encounter_object['encounter_datetime'])
    }
    response = create_response_object(status_code, encounter_object)
    return create_openhim_response_object(response, orchestration_results, properties)

def save_encounter(data):
    orchestration_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # validate patient
        cr_future = executor.submit(create_orchestration, 
                                    cr_url, 
                                    '/patient/{}'.format(data['patient_id']), 
                                    'Validate Patient Information', 
                                    'GET')
        # validate providers
        provider_futures = []
        for provider in data['providers']:
            provider_future = executor.submit(create_orchestration, 
                            hwr_url,
                            '/provider/{}'.format(provider['provider_id']),
                            'Validate Provider',
                            'GET')
            provider_futures.append(provider_future)
        # validate facility
        facility_future = executor.submit(create_orchestration,
                                          fr_url,
                                          '/location/{}'.format(data['location_id']),
                                          'Validate Location',
                                          'GET')

        orchestration_results.append(cr_future.result()[1])
        for i in range(len(data['providers'])):
            orchestration_results.append(provider_futures[i].result()[1])
        orchestration_results.append(facility_future.result()[1])

    encounter_id, orchestration, status_code = create_orchestration(shr_url,
                                                                    '/encounters',
                                                                    'Create Encounter',
                                                                    'POST',
                                                                    headers={'Content-Type': 'application/json'},
                                                                    request_body=data)
    orchestration_results.append(orchestration)

    properties = {
        'patient id': data['patient_id'],
        'encounter id': encounter_id
    }
    response = create_response_object(status_code, {'encounter_id': encounter_id})
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
            'body': json.dumps(request_body),
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
        'body': json.dumps(body),
        'timestamp': str(int(datetime.datetime.now().timestamp()*100))
    }

def create_properties_object(patient, encounters):
    properties = {
        'patient name': patient['family_name'] + ', ' + patient['given_name'],
        'city': patient['city'],
        'gender': patient['gender']
    }
    for i in range(len(encounters)):
        properties['Encounter {}'.format(i + 1)] = '{}, {}, {}'.format(encounters[i]['encounter_type_description'], 
                                                                        encounters[i]['location_name'], 
                                                                        encounters[i]['encounter_datetime'])
    return properties