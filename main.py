from functools import lru_cache
from collections import defaultdict
import time, requests # type: ignore
import json
import os

# change these to suit your environment
API_ENDPOINT="http://192.168.2.200:9000"
API_USER=""
API_PASS=""

# the class
class StreamAPI:

    # fire it up, and set the internal defaults
    def __init__( self, base_url: str, username: str, password: str ):
        self.base_url = base_url.rstrip( '/' )
        self.username = username
        self.password = password
        self._auth_headers = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    # hold the authentication headers
    @property
    def auth_headers( self ):

        # if the headers don't currently exist
        if self._auth_headers is None:

            # get out API tokens
            tokens = self._authenticate_with_retry( )

            # setup the internal headers
            self._auth_headers = {
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        
        # return them by default
        return self._auth_headers
    
    # setup the common exception thrower
    def _exception( self, e, error_msg ):

        # if there's no response
        if e.response is not None:

            # append the response status and text to the existing message
            error_msg += f": {e.response.status_code} - {e.response.text}"
        
        # now force the exception
        raise Exception( error_msg ) from e

    # let's try to authenticate against the API a configurable number of tries
    def _authenticate_with_retry( self ):

        # for each attempt in the retry number
        for attempt in range( self.max_retries ):
            
            # give it a shot...
            try:
                return self._authenticate( )
            
            # whooops, there was an issue this round...
            except requests.exceptions.RequestException as e:

                # if we're done trying...
                if attempt == self.max_retries - 1:
                    raise

                # print a message and wait a few seconds...
                print( f"Authentication failed (attempt {attempt + 1}), retrying..." )
                time.sleep( self.retry_delay )

    # make sure we cache the authentication for the app, only in memory, and only as long as it's running
    @lru_cache( maxsize=16 )
    def _authenticate( self ):

        # give it a shot
        try:

            # setup the response
            response = requests.post(
                f"{self.base_url}/api/accounts/token/",
                json={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/json"},
                timeout=30  # seconds
            )

            # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
            response.raise_for_status( )

            # return the response
            return response.json( )
        
        # whoopsie...
        except requests.exceptions.RequestException as e:

            # there was an issue, raise an excpetion with our intial message
            error_msg = "Authentication failed"

            # force the exception
            self._exception( e, error_msg )

    # trigger a M3U Account refresh
    def _trigger_refresh( self ):

        # give it a shot
        try:

            # setup the response
            response = requests.post(
                f"{self.base_url}/api/m3u/refresh/",
                headers=self.auth_headers,
                timeout=30  # seconds
            )

            # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
            response.raise_for_status( )

            # a 202 response code is valid, so if weve got it, just return
            if response.status_code == 202:
                return

        # whoopsie...
        except requests.exceptions.RequestException as e:

            # setup the exception message
            error_msg = "Refresh failed"

            # force the exception
            self._exception( e, error_msg )

    # get our streams from the M3U Accounts
    def _get_streams( self ):

        # trigger a m3u account refresh first
        self._trigger_refresh( )

        # give it a shot
        try:

            # setup the response
            response = requests.get(
                f"{self.base_url}/api/channels/streams/?page_size=2500", # page size may need to be increased/decreased based on your usage... I wanted to ensure I got all of mine...
                headers=self.auth_headers,
                timeout=30  # seconds
            )

            # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
            response.raise_for_status( )

            # get the response json
            data = response.json( )

            # if the desired "results" do not exist... raise an exception
            if 'results' not in data:
                raise ValueError( "API response missing 'results' field" )
            
            # return the data results only
            return data['results']
        
        # whoopsie...
        except requests.exceptions.RequestException as e:

            # setup the exception message
            error_msg = "Failed to fetch streams"

            # force the exception
            self._exception( e, error_msg )

    # get the existing channels if there are any
    def _get_channels(self):

        # give it a shot
        try:

            # setup the response
            response = requests.get(
                f"{self.base_url}/api/channels/channels/?page_size=2500", # page size may need to be increased/decreased based on your usage... I wanted to ensure I got all of mine...
                headers=self.auth_headers,
                timeout=30  # seconds
            )

            # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
            response.raise_for_status( )

            # get the response json
            data = response.json( )

            # return it
            return data
        
        # whoopsie...
        except requests.exceptions.RequestException as e:

            # setup the exception message
            error_msg = "Failed to fetch channels"

            # force the exception
            self._exception( e, error_msg )

    # create the channels
    def create_channels( self ):

        # give it a shot
        try:

            # grab all our streams
            print( "Fetching streams..." )
            streams = self._get_streams( )
            print( f"Found {len(streams)} streams" )

            # grab all our channels
            print( "Fetching channels..." )
            channels = self._get_channels( )
            print( f"Found {len(channels)} channels" )

            # setup the channel groups
            channel_groups = defaultdict( list )

            # loop the streams
            for stream in streams:

                # if we dont actually have a stream
                if not isinstance( stream, dict ):

                    # skip this iteration
                    continue

                # if we do not have an id or name for the stream...
                if 'id' not in stream or 'name' not in stream:

                    # skip this iteration
                    continue

                # create our grouping
                channel_groups[stream['name']].append( { 
                    'id': stream['id'],
                    'logo_url': stream['logo_url'],
                    'tvg_id': stream['tvg_id'],
                    'channel_group': stream['channel_group'],
                    'm3u_account': stream['m3u_account'],
                } )

            # After populating channel_groups, sort each group:
            for channel_name, streams in channel_groups.items( ):
                channel_groups[channel_name] = sorted(
                    streams,
                    key=lambda x: x['m3u_account'],  # Sort by this field, of you want to sort by another field, check the above for whats available...
                )

            # hold our results
            results = []

            # loop over the created/sorted channel groups
            for channel_name, streams in channel_groups.items( ):

                # get a channel ID if we have a match for the existing channels list
                channel_id = next( ( item.get( "id" ) for item in ( channels or [] ) if item.get( "name" ) == channel_name ), None )

                # if we do have a channel
                if channel_id:

                    # ----------- UPDATE 
                    # give this a shot
                    try:

                        # grab a response from attempting to PUT the updated data
                        response = requests.put(
                            f"{self.base_url}/api/channels/channels/{channel_id}/",
                            json={
                                'name': channel_name,
                                'streams': [stream['id'] for stream in streams],
                                'tvg_id': next( ( s['tvg_id'] for s in streams if s.get( 'tvg_id' ) not in [None, ''] ), None ),
                                'channel_group_id': next( ( s['channel_group'] for s in streams if s.get( 'channel_group' ) not in [None, ''] ), None )
                            },
                            headers=self.auth_headers,
                            timeout=30 # seconds
                        )

                        # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
                        response.raise_for_status()
                        
                        # append the response to the results and show a message
                        results.append( response.json( ) )
                        print( f"Updated channel: {channel_name}" )
                        print( f"{len(streams)} Streams" )

                    # whoopsie...
                    except requests.exceptions.RequestException as e:
                        
                        # setup the exception message
                        error_msg = f"Failed to update channel {channel_name}"

                        # force the exception
                        self._exception( e, error_msg )
                        
                        # continue on
                        continue

                    # we're golden here, continue on
                    continue

                # ----------- CREATE 
                # give this a shot
                try:

                    # hold the initial stream ID
                    _stream_id = next( ( s['id'] for s in streams if s.get( 'id' ) not in [None, ''] ), None )

                    # make sure we've got a stream ID.  really can't create a channel without it
                    if _stream_id:

                        # create the channel from the initial stream
                        response = requests.post(
                            f"{self.base_url}/api/channels/channels/from-stream/",
                            json={
                                'name': channel_name,
                                'stream_id': _stream_id
                            },
                            headers=self.auth_headers,
                            timeout=30 # seconds
                        )

                        # make sure we're raising an exception if an HTTP 4xx/5xx ocurrs
                        response.raise_for_status( )

                        # hold the response
                        _resp = response.json( )

                        # hold the channel id
                        _chan_id = _resp.get( 'id' )

                        # update the channel with all streams except the one we added the channel with
                        requests.put(
                            f"{self.base_url}/api/channels/channels/{_chan_id}/",
                            json={
                                'name': channel_name,
                                'streams': [stream['id'] for stream in streams],
                                'tvg_id': next( ( s['tvg_id'] for s in streams if s.get( 'tvg_id' ) not in [None, ''] ), None ),
                                'channel_group_id': next( ( s['channel_group'] for s in streams if s.get( 'channel_group' ) not in [None, ''] ), None )
                            },
                            headers=self.auth_headers,
                            timeout=30 # seconds
                        )

                        # append the response to the results and show a message
                        results.append( _resp )
                        print( f"Created channel: {channel_name}" )
                        print( f"{len(streams)} Streams" )

                    # otherwise, show that it chould not be created
                    else:
                        print( f"Could Not Create Channel: {channel_name}" )
                    
                # whoopsie...
                except requests.exceptions.RequestException as e:

                    # setup the exceptions message
                    error_msg = f"Failed to create channel {channel_name}"

                    # force the exception
                    self._exception( e, error_msg )
                    
                    # continue on
                    continue

            # now return our results
            return results


        # whoopsie
        except Exception as e:

            # show the exceptions message(s)
            print( f"Error in create_channels: {str(e)}" )
            raise

# the mainn app
if __name__ == "__main__":

    # give it a shot
    try:
        config_file = 'config.json'
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)

        API_ENDPOINT = config['API_ENDPOINT']
        API_USER = config['API_USER']
        API_PASS = config['API_PASS']

        # fire up the class
        api = StreamAPI( API_ENDPOINT, API_USER, API_PASS )
        
        # attempt to update or create the channels
        print( "Starting channel creation..." )
        results = api.create_channels( )
        print( f"Successfully created {len(results)} channels" )
        
    # whoopsie
    except Exception as e:

        # show the exception
        print( f"Fatal error: {str(e)}" )
        
