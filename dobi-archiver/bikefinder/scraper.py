import json
import logging
import os

import boto3
import requests
from attr import asdict
from lambda_decorators import no_retry_on_failure

from bikefinder.models import Bike, Bikes
from bikefinder.util import database, fully_unwrap_function, search_points


BIKESHARE_URL = 'http://feeds.capitalbikeshare.com/stations/stations.json'
MOBIKE_GBFS_URL = 'https://mobike.com/us/gbfs/v1/free_bike_status'
MOBIKE_URL = 'https://mwx.mobike.com/mobike-api/rent/nearbyBikesInfo.do'
LIMEBIKE_URL = 'https://lime.bike/api/partners/v1/bikes'
LIMEBIKE_HEADERS = {'Authorization': 'Bearer limebike-PMc3qGEtAAXqJa'}
LIMEBIKE_PARAMS = {'region': 'Washington DC Proper'}
OFO_URL = 'http://ofo-global.open.ofo.com/api/bike'
OFO_DATA = {
    'token':'c902b87e3ce8f9f95f73fe7ee14e81fe',
    'name':'Washington',
}


logger = logging.getLogger(__name__)

def save_to_db(bikes, db):
    for bike in bikes:
        db.query("""
                 insert into bike_locations (provider, bike_id, location, raw)
                 values (:provider, :bike_id, :location, :raw)
                 """, **asdict(bike))

@no_retry_on_failure
@database
def scrape_jump(event, context):
    resp = requests.get('https://dc.jumpmobility.com/opendata/free_bike_status.json')
    bikes = Bikes.from_gbfs_json(resp.json(), 'JUMP')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_spin(event, context):
    resp = requests.get('https://web.spin.pm/api/gbfs/v1/free_bike_status')
    bikes = Bikes.from_gbfs_json(resp.json(), 'spin')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_bird(event, context):
    resp = requests.get('https://gbfs.bird.co/dc')
    bikes = Bikes.from_gbfs_json(resp.json(), 'bird')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_lyft(event, context):
    resp = requests.get('https://s3.amazonaws.com/lyft-lastmile-production-iad/lbs/dca/free_bike_status.json')
    bikes = Bikes.from_gbfs_json(resp.json(), 'lyft')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_skip(event, context):
    resp = requests.get('https://us-central1-waybots-production.cloudfunctions.net/dcFreeBikeStatus')
    bikes = Bikes.from_gbfs_json({'data': resp.json()}, 'skip')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_mobike_gbfs(event, context):
    resp = requests.get('https://mobike.com/us/gbfs/v1/free_bike_status')
    bikes = Bikes.from_gbfs_json(resp.json(), 'mobike')
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_limebike(event, context):
    resp = requests.get(
        LIMEBIKE_URL,
        headers=LIMEBIKE_HEADERS,
        params=LIMEBIKE_PARAMS,
    )
    bikes = Bikes.from_limebike_json(resp.json())
    save_to_db(bikes, context.db)
    return bikes.geojson

@no_retry_on_failure
@database
def scrape_ofo(event, context):
    resp = requests.post(
        OFO_URL,
        data=OFO_DATA,
    )
    bikes = Bikes.from_ofo_json(resp.json())
    save_to_db(bikes, context.db)
    return bikes.geojson

async def fetch(session, url):
        async with session.get(url) as response:
            return await response.json()

async def get_mobike(session, lat, lng):
    resp = await session.post(
        MOBIKE_URL,
        params={
            'longitude': str(lng),
            'latitude': str(lat)
        },
        headers={'Referer': 'https://servicewechat.com/'},
    )
    try:
        bikes = Bikes.from_mobike_json(await resp.json())
        print(f'found {len(bikes)} at {lat}, {lng}')
        return bikes
    except:
        print(f'{resp.status_code} response')

@database
def scrape_mobike(event, context):
    if event.get('coords') is None:
        for lat, lng in search_points():
            boto3.client('lambda').invoke(
                InvocationType='Event',
                FunctionName=f'bikefinder-{os.environ["STAGE"]}-scrape_mobike',
                Payload=json.dumps({'coords': [lat, lng]}))
    else:
        lat, lng = event['coords']
        resp = requests.post(MOBIKE_URL, params={
            'longitude': str(lng),
            'latitude': str(lat)
        }, headers={'Referer': 'https://servicewechat.com/'})
        bikes = Bikes.from_mobike_json(resp.json())
        save_to_db(bikes, context.db)
        print(f'found {len(bikes)} at {lat}, {lng}')
        return bikes.geojson
