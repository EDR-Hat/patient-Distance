import requests
import json
import sys
import pandas as pd
import math
import haversine as hs
from haversine import Unit

#does the API call to the census geocoding
#returns error codes if API has a result, such as a not found issue
def req(address, city):
    endpoint = 'https://geocoding.geo.census.gov/geocoder/locations/address'
    if str(address) == '':
        return ''
    params = {}
    params['street'] = str(address).replace(' ', '+')
    params['state'] = 'CA'
    params['benchmark'] = '2020'
    params['format'] = 'json'
    params['city'] = city
    r = requests.get(endpoint, params=params)
    if r.status_code != 200:
        return 1
    info = r.json()
    if len(info['result']['addressMatches']) == 0:
        return 2
    if len(info['result']['addressMatches']) != 1:
        return 3
    return (info['result']['addressMatches'][0]['coordinates']['x'], info['result']['addressMatches'][0]['coordinates']['y'])

#does a haversine approximation (has %0.5 error) of distances on earth
#if there is an error code, makes it negative to signify it is an error
#-1: api returned a status code besides 200
#-2: api couldn't find listed address
#-3: api found multiple lat lon pairs for that address
def sanatize(row, place_list):
    if isinstance(row, int):
        return row * -1
    return shortestDist((float(row[1]), float(row[0])), place_list)[0]

#returns a tuple of the shortest distance (in miles)
# and the lat and lon from the patient for that distance
def shortestDist(patient_tup, list_of_location_tups):
    lengths = [hs.haversine(patient_tup, x) for x in list_of_location_tups]
    return sorted(zip(lengths, list_of_location_tups))[0]

#helper function if you don't have tuples
def dist(lat1, lon1, lat2, lon2):
    return hs.haversine((lat1, lon1), (lat2, lon2), unit=Unit.MILES)

#reads two data frames for the relevant information
#returns a data frame of the shortest distance to a
#care facility and the patient id
def getDistances(patients, locations):
    for required in ['id', 'address_line_one', 'city']:
        if required not in patients.columns:
            print(required + ' is not found in patients dataframe')
            exit(1)

    for required in ['lat', 'lon']:
        if required not in locations.columns:
            print(required + ' is not found in locations dataframe')
            exit(1)

    locations = locations.dropna()
    tup = list(zip(locations['lat'], locations['lon']))
    coord = patients.apply(lambda x: req(x['address_line_one'], x['city']), axis=1)
    distMi = [sanatize(y, tup) for y in coord]

    fin = pd.DataFrame(distMi, columns=['dist mi'])
    fin['id'] = patients['id'].copy(deep=True)
    return fin


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: " + sys.argv[0] + " [patient addresses csv] [care locations csv]")
        exit(1)

    try:
        patients = pd.read_csv(sys.argv[1])
    except:
        print('file open failed for patient data csv path: ' + sys.argv[1])
        exit(1)

    try:
        locations = pd.read_csv(sys.argv[2])
    except:
        print('file open failed for location data csv path: ' + sys.argv[2])
        exit(1)
    
    patientDistances = getDistances(patients, locations)
    print(patientDistances)