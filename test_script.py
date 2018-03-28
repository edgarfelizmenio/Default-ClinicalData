import requests
import datetime

# fetch encounter
response = requests.get('{}/encounters/101'.format(shr_url))

print(response.json())
print(response.headers)

patient_id = 101

encounter1 = {
    'providers': [{
        'provider_id': 1,
        'encounter_role_id': 1,
        }],
    'location_id': 1,
    'patient_id': patient_id,
    'encounter_type': 1,
    'observations': [{
        'person_id': patient_id,
        'concept_id': 666,
        'obs_datetime': str(datetime.datetime.now()),
        'location_id': 1,
        'value_boolean': False,
        'comments': "no comment"
    }, {
        'person_id': patient_id,
        'concept_id': 999,
        'obs_datetime': str(datetime.datetime.now()),
        'location_id': 1,
        'value_datetime': str(datetime.datetime.now()),
        'comments': 'ganun talaga eh' 
    }],
    'encounter_datetime': str(datetime.datetime.now())
}

encounter2 = {
    'providers': [{
        'provider_id': 1,
        'encounter_role_id': 1,
        }],
    'location_id': 1,
    'encounter_type': 1,
    'observations': [{
        'person_id': patient_id,
        'concept_id': 69,
        'obs_datetime': str(datetime.datetime.now()),
        'location_id': 1,
        'value_boolean': True,
        'comments': "may comment"
    }, {
        'person_id': patient_id,
        'concept_id': 69,
        'obs_datetime': str(datetime.datetime.now()),
        'location_id': 1,
        'value_coded_name_id': 6969,
        'comments': "may comment"
    }],
    'encounter_datetime': str(datetime.datetime.now())
}

headers = {'Content-Type': 'application/json'}
response1 = requests.post('{}/encounters/'.format(shr_url), json=encounter1, headers=headers)
response2 = requests.post('{}/encounters/{}'.format(shr_url, patient_id), json=encounter2, headers=headers)

print("response 1:", response1, response1.json(), response1.headers)
print()
print("response 2:", response2, response2.json(), response2.headers) 