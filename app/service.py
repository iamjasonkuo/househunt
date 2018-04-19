import base64
import json
import requests
import xmltodict
import boto3, botocore
import os
import sys

from flask import current_app
from app.helper import Place, Error, prepFullAddressSearch
from xmlrpc.client import ServerProxy, Fault
from hashlib import md5
from queue import Queue
from threading import Thread

try:
  # python 3
  from urllib.parse import urlparse, urlunparse, urlencode, quote
  from urllib.request import urlopen
  from urllib.request import __version__ as urllib_version
except ImportError:
  from urlparse import urlparse, urlunparse
  from urllib2 import urlopen
  from urllib import urlencode
  from urllib import __version__ as urllib_version

class AWS_api(object):

    def __init__(self):
        if 'S3_ACCESS_KEY' not in current_app.config or \
            not current_app.config['S3_ACCESS_KEY']:
                return 'Error: the AWS S3_ACCESS_KEY is not configured.'
        self.base_url = "http://{}.s3.amazonaws.com/".format(current_app.config['S3_BUCKET_NAME'])
        self._input_encoding = None
        self._request_headers=None
        self.__auth = None
        self._timeout = None
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=current_app.config['S3_ACCESS_KEY'],
            aws_secret_access_key=current_app.config['S3_SECRET_ACCESS_KEY']
            )

    def upload_fileobj(filename, bucket, key, acl="public-read"):
        print('INSIDE AWS_UPLOADFILEOBJ FILENAME: {}'.format(filename.__dict__))
        try:
            with open(filename, 'rb') as data:
                self.s3.upload_fileobj(
                    data,
                    bucket,
                    key,
                    ExtraArgs={
                        "ACL": acl,
                        "ContentType": file.content_type
                    }
                )
        except Exception as e:
            print("Something Happened: ", e)
            return e
        return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)

    def upload_file_to_s3(self, file, bucket_name, acl="public-read"):
        try:
            self.s3.upload_fileobj(
                file,
                bucket_name,
                file.filename,
                ExtraArgs={
                    "ACL": acl,
                    "ContentType": file.content_type
                }
            )
        except Exception as e:
            print("Something Happened: ", e)
            return e
        return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)


class GoogleMaps_api(object):
    def __init__(self):
        if 'GOOGLEMAPS_KEY' not in current_app.config or \
                not current_app.config['GOOGLEMAPS_KEY']:
            return 'Error: the google maps GOOGLEMAPS_KEY is not configured.'

        if 'GOOGLEMAPS_GEOCODING_KEY' not in current_app.config or \
                not current_app.config['GOOGLEMAPS_GEOCODING_KEY']:
            return 'Error: the google maps GOOGLEMAPS_GEOCODING_KEY is not configured.'

        self.base_url = "https://maps.googleapis.com/maps/api"
        self._input_encoding = None
        self._request_headers=None
        self.__auth = None
        self._timeout = None

    def getGeocode(self, address, city, state):
        principal_place = prepFullAddressSearch(address, city, state)
        address = address.replace(' ', '+')
        city = city.replace(' ', '+')
        key = current_app.config['GOOGLEMAPS_GEOCODING_KEY']

        r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={},+{},+{}&key={}'.format(address, city, state, key))
        if r.status_code != 200:
            return 'Error: the geocoding service failed.'
        #TODO: If zero results then return raise error
        parsed = json.loads(r.content.decode('utf-8-sig'))
        print(json.dumps(parsed, indent=4, sort_keys=True))
        #TODO: Refactor and clean up data acquisition
        output = {
            'principal': principal_place,
            'lat': parsed['results'][0]['geometry']['location']['lat'],
            'lng': parsed['results'][0]['geometry']['location']['lng']
        }
        return output


class Zillow_api(object):
    def __init__(self):
        if 'ZWSID' not in current_app.config or \
                not current_app.config['ZWSID']:
            return 'Error: the zillow ZWSID is not configured.'

        self.base_url = "https://www.zillow.com/webservice"
        self._input_encoding = None
        self._request_headers=None
        self.__auth = None
        self._timeout = None

    def _RequestUrl(self, url, verb, data=None):
        """
        Request a url.
        :param url: The web location we want to retrieve.
        :param verb: GET only (for now).
        :param data: A dict of (str, unicode) key/value pairs.
        :return:A JSON object.
        """
        if verb == 'GET':
            url = self._BuildUrl(url, extra_params=data)
            try:
                return requests.get(
                    url,
                    auth=self.__auth,
                    timeout=self._timeout
                )
            except requests.RequestException as e:
                raise Error(str(e))
        return 0

    def _BuildUrl(self, url, path_elements=None, extra_params=None):
        """
        Taken from: https://github.com/bear/python-twitter/blob/master/twitter/api.py#L3814-L3836
        :param url:
        :param path_elements:
        :param extra_params:
        :return:
        """
        # Break url into constituent parts
        (scheme, netloc, path, params, query, fragment) = urlparse(url)

        # Add any additional path elements to the path
        if path_elements:
            # Filter out the path elements that have a value of None
            p = [i for i in path_elements if i]
            if not path.endswith('/'):
                path += '/'
            path += '/'.join(p)

        # Add any additional query parameters to the query string
        if extra_params and len(extra_params) > 0:
            extra_query = self._EncodeParameters(extra_params)
            # Add it to the existing query
            if query:
                query += '&' + extra_query
            else:
                query = extra_query

        # Return the rebuilt URL
        return urlunparse((scheme, netloc, path, params, query, fragment))

    def _EncodeParameters(self, parameters):
        """
        Return a string in key=value&key=value form.
        :param parameters: A dict of (key, value) tuples, where value is encoded as specified by self._encoding
        :return:A URL-encoded string in "key=value&key=value" form
        """

        if parameters is None:
            return None
        else:
            return urlencode(dict([(k, self._Encode(v)) for k, v in list(parameters.items()) if v is not None]))

    def _Encode(self, s):
        if self._input_encoding:
            return str(s, self._input_encoding).encode('utf-8')
        else:
            return str(s).encode('utf-8')

    def getDeepSearchResults(self, address, citystatezip, rentzestimate=False):
        url = '{}/GetDeepSearchResults.htm'.format(self.base_url)
        parameters = {'zws-id': current_app.config['ZWSID'],
                      'address': address,
                      'citystatezip': citystatezip
                      }
        if rentzestimate:
            parameters['rentzestimate'] = 'true'
        resp = self._RequestUrl(url, 'GET', data=parameters)
        data = resp.content.decode('utf-8')
        xmltodict_data = xmltodict.parse(data)
        place = Place(has_extended_data=True)
        try:
            place.set_data(xmltodict_data.get('SearchResults:searchresults', None)['response']['results']['result'])
        except:
            raise Error({'message': "Zillow did not return a valid response: %s" % data})
        return place

    def getDeepComps(self, zpid, count=10, rentzestimate=False):
        url = '%s/GetDeepComps.htm' % (self.base_url)
        parameters = {'zws-id': current_app.config['ZWSID'],
                      'zpid': zpid,
                      'count': count}
        if rentzestimate:
            parameters['rentzestimate'] = 'true'
        resp = self._RequestUrl(url, 'GET', data=parameters)
        data = resp.content.decode('utf-8')
        # transform the data to an dict-like object
        xmltodict_data = xmltodict.parse(data)
        # get the principal property data
        principal_place = Place()
        principal_data = xmltodict_data.get('Comps:comps')['response']['properties']['principal']
        try:
            principal_place.set_data(principal_data)
        except:
            raise Error({'message': 'No principal data found: %s' % data})
        # get the comps property_data
        comps = xmltodict_data.get('Comps:comps')['response']['properties']['comparables']['comp']
        comp_places = []
        for datum in comps:
            place = Place()
            try:
                place.set_data(datum)
                comp_places.append(place)
            except:
                raise Error({'message': 'No valid comp data found %s' % datum})
        output = {
            'principal': principal_place,
            'comps': comp_places
        }
        return output

    def getZestimate(self, zpid, rentzestimate=False):
        url = '%s/GetZestimate.htm' % (self.base_url)
        parameters = {'zws-id': current_app.config['ZWSID'],
                      'zpid': zpid}
        if rentzestimate:
            parameters['rentzestimate'] = 'true'
        resp = self._RequestUrl(url, 'GET', data=parameters)
        data = resp.content.decode('utf-8')
        xmltodict_data = xmltodict.parse(data)
        place = Place()
        try:
            place.set_data(xmltodict_data.get('Zestimate:zestimate', None)['response'])
        except:
            raise ZillowError({'message': "Zillow did not return a valid response: %s" % data})
        return place

class GravatarXMLRPC(object):
    API_URI = 'https://secure.gravatar.com/xmlrpc?user={0}'

    def __init__(self, request, password=''):
        self.request = request
        self.password = password
        self.email = sanitize_email(request.user.email)
        self.email_hash = md5_hash(self.email)
        self._server = ServerProxy(
            self.API_URI.format(self.email_hash))

    def saveData(self, image):
        """ Save binary image data as a userimage for this account """
        params = { 'data': base64_encode(image.read()), 'rating': 0, }
        return self._call('saveData', params)
        #return self.useUserimage(image)

    def _call(self, method, params={}):
        """ Call a method from the API, gets 'grav.' prepended to it. """
        args = { 'password': self.password, }
        args.update(params)

        try:
            return getattr(self._server, 'grav.' + method, None)(args)
        except Fault as error:
            error_msg = "Server error: {1} (error code: {0})"
            print(error_msg.format(error.faultCode, error.faultString))


def base64_encode(obj):
    return base64.b64encode(obj)

def sanitize_email(email):
    return email.lower().strip()

def md5_hash(string):
    return md5(string.encode('utf-8')).hexdigest()
