# -*- coding: UTF-8 -*-

import time
from urllib2 import urlopen
from urllib import urlencode

from django.utils import simplejson as json
from django.conf import settings

ADMIN_NAME, ADMIN_EMAIL = settings.ADMINS[0]
DEFAULT_CITY = settings.CITY

keys = getattr(settings, 'GEOCODE_KEYS', {})


class QuotaExceeded(Exception):
    """ The quota has been exceeded for this geocoder. 
        The query may succeed when tried again, in the near future. 
    """

class NoClearResult(Exception):
    """ This is a permanent error; query will not succeed with this geocoder. 
        It could mean that no results were return for the query, or that the 
        results were ambiguous.
    """

class Geocoder(object):
    # How many seconds to wait for the quota to be reset
    quota_reset = None

    # How slowly should queries be run, in seconds
    # Will of course only work for this thread/process
    rate_limit = None

    key = "UNKNOWN"

    def __init__(self):
        self.query = ""

    def geocode(self, values, require_exact=True):
        if 'city' not in values:
            values['city'] = DEFAULT_CITY
        params = self.get_params(values)
        if self.rate_limit is not None:
            time.sleep(self.rate_limit)
        self.query = urlencode(dict((unicode(k).encode("utf-8"),unicode(v).encode("utf-8")) for k, v in params.items()))
        response = urlopen(self.url + "?" + self.query)
        return self.parse_response(response.read(), require_exact)

class GoogleMaps(Geocoder):
    url = 'http://maps.googleapis.com/maps/api/geocode/json'

    # Quota is reset daily
    quota_reset = 60 * 60 * 24

    key = "GOOGLE"

    def get_params(self, values):
        params = {'sensor': 'false'}
        if 'country' in values:
            params['region'] = values['country']
        if 'language' in values:
            params['language'] = values['language']
        if 'address' in values:
            params['address'] = values['address']
        else:
            params['address'] = build_address(values, 'street', 'postal_code', 'locality', 'city')
        return params

    def parse_response(self, response, require_exact):
        data = json.loads(response)
        status = data['status']
        if status == "OVER_QUERY_LIMIT":
            raise QuotaExceeded()
        elif status == "ZERO_RESULTS":
            raise NoClearResult("Zero results returned")
        elif status != "OK":
            raise NoClearResult(status)
        results = data['results'] 
        if len(results) > 1:
            raise NoClearResult("Multiple results returned")

        result = results[0]
        if require_exact and 'street_address' not in result['types']:
            raise NoClearResult("Insufficiently accurate result returned")

        location = result['geometry']['location']

        return result['formatted_address'], (location['lat'], location['lng'])

        

class Nominatum(Geocoder):
    url = 'http://nominatim.openstreetmap.org/search'
    # Be nice to free services
    rate_limit = 0.5

    key = "NOMINATUM"

    def get_params(self, values):
        params = {'format': 'json', 'email': ADMIN_EMAIL}

        if 'country' in values:
            params['countrycodes'] = values['country']
        if 'language' in values:
            params['accept-language'] = values['language']
        if 'address' in values:
            params['q'] = values['address']
        else:
            params['q'] = build_address(values, 'street', 'postal_code', 'locality', 'city')

        return params

    def parse_response(self, response, require_exact):
        data = json.loads(response)
        results = data
        if len(results) == 0:
            raise NoClearResult("Zero results returned")
        elif len(results) > 1:
            raise NoClearResult("Multiple results returned")
        result = results[0]
        if require_exact and result['osm_type'] != 'node':
            raise NoClearResult("Insufficiently accurate result returned")
        
        return result['display_name'], (result['lat'], result['lon'])


class OpenMapQuest(Nominatum):
    url = 'http://open.mapquestapi.com/nominatim/v1/search'

    key = "OPENMAPQUEST"

    def get_params(self, values):
        params = super(OpenMapQuest, self).get_params(values)
        del params['email']
        return params


class Yahoo(Geocoder):
    url = 'http://where.yahooapis.com/geocode'

    key = "YAHOO"

    def get_params(self, values):
        params = { 'flags': 'JG', 'appid': keys.get('yahoo')}

        if 'country' in values:
            params['country'] = values['country']
        if 'language' in values:
            params['locale'] = values['language']
        # No results are returned when we use this
        #if 'name' in values:
        #    params['name'] = values['name']
        if 'address' in values:
            params['q'] = values['address']
        else:
            if 'street' in values:
                params['street'] = values['street']
            if 'postal_code' in values:
                params['postal'] = values['postal_code']
            if 'locality' in values:
                params['neighborhood'] = values['locality']
            if 'city' in values:
                params['city'] = values['city']

        return params

    def parse_response(self, response, require_exact):
        data = json.loads(response)
        results = data['ResultSet']
        status = results['Error']
        if status != "0":
            raise NoClearResult(status)
        found = int(results['Found'])
        if found == 0:
            raise NoClearResult("Zero results returned")
        elif found > 1:
            raise NoClearResult("Multiple results returned")

        result = results['Results'][0]
#        if require_exact and int(result['quality']) < 80:
#            raise NoClearResult("Insufficiently accurate result returned")

        fields = ['name', 'line1', 'line2', 'line3', 'line4']
        name = ', '.join(result[key] for key in fields if result[key])

        return name, (result['latitude'], result['longitude'])


def build_address(values, *fields):
    """ Create a single string to be passed as an "address", using the values dict. """

    if not fields:
        fields = ['street', 'postal_code', 'locality', 'city', 'country']

    return ', '.join(values[f] for f in fields if f in values)

