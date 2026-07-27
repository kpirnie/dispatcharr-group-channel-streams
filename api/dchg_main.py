from functools import lru_cache
from collections import defaultdict
import time
import requests
from typing import Dict, List, Optional, Any, DefaultDict
from utils.exceptions import APIException
import re

# this is the main class
class DCHG_Main:

    # fire it up!
    def __init__(self, base_url: str, username: str, password: str, normalizer: str, refresh: bool = False, prune: bool = False):
        
        # setup the internals
        self.base_url = base_url.rstrip( '/' )
        self.username = username
        self.password = password
        self.normalizer = normalizer
        self.refresh = refresh
        self._auth_headers: Optional[Dict[str, str]] = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.prune = prune

    # setup a property to hold our authentication headers
    @property
    def auth_headers( self ) -> Dict[str, str]:
        
        # if the aren't yet set
        if self._auth_headers is None:

            # grab the token from the api
            tokens = self._authenticate_with_retry( )

            # set the auth header
            self._auth_headers = {
                "Authorization": f"Bearer {tokens['access']}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

        # return the auth headers
        return self._auth_headers

    # handle our internal exceptions
    def _exception( self, e: requests.exceptions.RequestException, error_msg: str ) -> None:
        
        # if we have a response, setup the rest of the message
        if e.response is not None:
            error_msg += f": {e.response.status_code} - {e.response.text}"

        # raise our custom exception
        raise APIException( error_msg ) from e

    # attempt to authenticate a few times if necessary
    def _authenticate_with_retry(self) -> Dict[str, Any]:
        
        # loop the number of configured retries
        for attempt in range( self.max_retries ):
            
            # give it a shot
            try:

                # return the authentication
                return self._authenticate( )
            
            # whoops.. guess not this time...
            except requests.exceptions.RequestException as e:
                
                # see if we're beyond the configured number of tries
                if attempt == self.max_retries - 1:
                    raise

                # show a message about the retry and wait a little bit...
                print( f"Authentication failed (attempt {attempt + 1}), retrying..." )
                time.sleep( self.retry_delay )

        # oof...  NFG, throw our exception
        raise APIException( "Max authentication retries exceeded" )

    # authenticate, and cache the token
    @lru_cache( maxsize=16 )
    def _authenticate( self ) -> Dict[str, Any]:
        
        # give it a shot
        try:

            # setup the response POSTing to the API
            response = requests.post(
                f"{self.base_url}/api/accounts/token/",
                json={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # return the resonse (in this case, the token)
            return response.json( )
        
        # whoopsie... make sure to force the exception
        except requests.exceptions.RequestException as e:
            self._exception( e, "Authentication failed" )

    # trigger a regresh of the M3U accounts
    def _trigger_refresh( self ) -> None:
        
        # give it a shot
        try:

            # setup the response
            response = requests.post(
                f"{self.base_url}/api/m3u/refresh/",
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # make sure we've got a good response code
            if response.status_code == 202:
                return
            
        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Refresh failed" )

    # get all the streams
    def _get_streams( self ) -> List[Dict[str, Any]]:
        
        # if we're set to refresh, let's do that first
        if self.refresh:

            # trigger a refresh of the M3U accounts
            print( "Triggering M3U account refresh..." )
            self._trigger_refresh( )

            # wait a little bit for it to finish
            print( "Waiting for M3U refresh to complete..." )
            time.sleep( 10 )
            print( "M3U refresh complete, fetching streams..." )

        # give it a shot
        try:

            # hold all of the streams
            all_streams = []

            # start with the first page
            page = 1

            # loop while we have a page to fetch
            while True:

                # build the page url against our own base url
                url = f"{self.base_url}/api/channels/streams/?page_size=2500&page={page}"

                # setup the response from the API
                response = requests.get(
                    url,
                    headers=self.auth_headers,
                    timeout=30
                )

                # make sure we're setup to throw an actual error on an error status
                response.raise_for_status( )

                # hold the data
                data = response.json( )

                # if we don't have results in the data
                if 'results' not in data:
                    raise ValueError( "API response missing 'results' field" )

                # append this pages results
                all_streams.extend( data['results'] )

                # if there's no next page, we're done
                if not data.get( 'next' ):
                    break

                # otherwise, move to the next page
                page += 1

            # return the full set
            return all_streams
        
        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Failed to fetch streams" )

    # get all our channels if any exist
    def _get_channels( self ) -> List[Dict[str, Any]]:
        
        # let's give it a shot
        try:

            # hold the response
            response = requests.get(
                f"{self.base_url}/api/channels/channels/?page_size=2500",
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # hold the data
            data = response.json( )

            # if the response is paginated, return the results, otherwise it's already a list
            return data['results'] if isinstance( data, dict ) else data
        
        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Failed to fetch channels" )

    # normalize channel names
    def _normalize_channel_name(self, name: str) -> str:

        # make sure the normalizer argument is a valid regex string
        try:
            # Test if the pattern compiles (this checks if it's a valid regex)
            compiled = re.compile( self.normalizer )
            
            # If it compiles, perform the replacement
            return compiled.sub( "", name )
        
        # whoops...
        except re.error:

            # If it's not a valid regex, return the original text
            return name

    # group and sort the streams
    def _group_and_sort_streams( self, streams: List[Dict[str, Any]] ) -> Dict[str, List[Dict[str, Any]]]:
        
        # setup the channel groups
        channel_groups: DefaultDict[str, List[Dict[str, Any]]] = defaultdict( list )
        
        # loop over teh streams
        for stream in streams:

            # make sure we've got all the data we need
            if not isinstance( stream, dict ) or 'id' not in stream or 'name' not in stream:
                continue

            # normalize the stream name
            stream_name = self._normalize_channel_name( stream['name'] )
                
            # setup the grouped channels streams
            channel_groups[stream_name].append( {
                'id': stream['id'],
                'logo_url': stream.get( 'logo_url', 'https://cdn.kevp.us/tv/kptv-icon.png' ),
                'tvg_id': stream.get( 'tvg_id' ),
                'channel_group': stream.get( 'channel_group' ),
                'm3u_account': stream.get( 'm3u_account' ),
            } )

        # return the sorted (by the account name)
        return {
            name: sorted( group, key=lambda x: x['m3u_account'] )
            for name, group in channel_groups.items( )
        }

    # find the channel id by name if it exists
    def _find_channel_id( self, channels: List[Dict[str, Any]], channel_name: str ) -> Optional[int]:
        
        # return the channel id
        return next(
            ( item.get( "id" ) for item in ( channels or [] ) 
             if item.get( "name" ) == channel_name ),
            None
        )

    # update an existing data with new stream dat
    def _update_channel( self, channel_id: int, channel_name: str, streams: List[Dict[str, Any]] ) -> Optional[Dict[str, Any]]:
        
        # give it a shot
        try:

            # setup the response
            response = requests.put(
                f"{self.base_url}/api/channels/channels/{channel_id}/",
                json={
                    'name': channel_name,
                    'streams': [stream['id'] for stream in streams],
                    'tvg_id': self._get_first_valid( streams, 'tvg_id' ),
                    'channel_group_id': self._get_first_valid( streams, 'channel_group' )
                },
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # return the json response
            return response.json( )
        
        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, f"Failed to update channel {channel_name}" )

    # create a new channel with all streams necessary
    def _create_channel( self, channel_name: str, streams: List[Dict[str, Any]] ) -> Optional[Dict[str, Any]]:
        
        # give it a shot
        try:

            # get the first stream id
            initial_stream_id = self._get_first_valid( streams, 'id' )

            # if we do not have one...
            if not initial_stream_id:
                print(f"Could Not Create Channel: {channel_name} (no valid stream ID)")
                return None

            # Create channel from initial stream
            response = requests.post(
                f"{self.base_url}/api/channels/channels/from-stream/",
                json={
                    'name': channel_name,
                    'stream_id': initial_stream_id
                },
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # grab the channel data
            channel_data = response.json( )

            # Update the new channel with all streams
            if channel_id := channel_data.get( 'id' ):

                # grab the update results and return the results
                update_result = self._update_channel( channel_id, channel_name, streams )
                return update_result if update_result else channel_data

            # return the channel data    
            return channel_data
        
        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, f"Failed to create channel {channel_name}" )

    # get the first valid item
    def _get_first_valid( self, items: List[Dict[str, Any]], key: str ) -> Any:
        
        # return it
        return next( ( item[key] for item in items if item.get( key ) not in [None, ''] ), None )

    # log/show the action taken
    def _log_channel_action( self, channel_name: str, streams: List[Dict[str, Any]], exists: bool = False ) -> None:
        
        # what action is taken... then print it
        action = "Updated" if exists else "Created"
        print( f"{action} channel: {channel_name}" )
        print( f"{len(streams)} Streams" )

    # prune stale streams from dispatcharr entirely
    def _prune_stale_streams( self, channels: List[Dict[str, Any]], streams: List[Dict[str, Any]] ) -> None:

        # hold the ids of all stale streams
        stale_ids = [stream['id'] for stream in streams if isinstance( stream, dict ) and stream.get( 'is_stale', False )]

        # nothing stale, move along
        if not stale_ids:
            print( "No stale streams found" )
            return

        # give it a shot
        try:

            # bulk delete the stale streams
            response = requests.delete(
                f"{self.base_url}/api/channels/streams/bulk-delete/",
                json={ 'stream_ids': stale_ids },
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # log/print what we pruned
            print( f"{len(stale_ids)} Stale Streams Deleted" )

        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Failed to bulk delete stale streams" )

    # run the channel creator/updater
    def create_channels( self ) -> List[Dict[str, Any]]:

        # give it a shot
        try:

            # grab all streams first
            print( "Fetching streams..." )
            streams = self._get_streams( )
            print( f"Found {len(streams)} streams" )
            
            # grab all existing streams
            print( "Fetching channels..." )
            channels = self._get_channels( )
            print( f"Found {len(channels)} channels" )

            # if we're set to prune, remove stale streams from the channels first
            if self.prune:
                print( "Pruning stale streams..." )
                self._prune_stale_streams( channels, streams )

                # filter the stale streams out so grouping doesn't re-add them
                streams = [stream for stream in streams if not stream.get( 'is_stale', False )]

            # setup and hold the grouped/sorted channels
            channel_groups = self._group_and_sort_streams( streams )

            # hold the results
            results = []

            # loop over the channel groups
            for channel_name, streams in channel_groups.items( ):

                # grab a channel id
                channel_id = self._find_channel_id( channels, channel_name )
                
                # if we have it
                if channel_id:

                    # update the channel
                    result = self._update_channel( channel_id, channel_name, streams )
                
                # otherwise
                else:

                    # create the channel
                    result = self._create_channel(channel_name, streams)

                # if we have a result                
                if result:

                    # append them
                    results.append( result )

                    # log/print the action we took
                    self._log_channel_action( channel_name, streams, exists=bool( channel_id ) )
                    
            # return the results
            return results

        # whoopsie...
        except Exception as e:
            print( f"Error in create_channels: {str(e)}" )
            raise

    # export the channels to stdout
    def export_channels( self ) -> None:

        # give it a shot
        try:

            # grab all existing channels
            channels = self._get_channels( )

            # print the header row
            print( '"Channel Name","tvg-id"' )

            # loop over the channels sorted by name
            for channel in sorted( channels, key=lambda c: str( c.get( 'name', '' ) ).lower( ) ):

                # quote-wrap and escape the fields
                name = str( channel.get( 'name', '' ) ).replace( '"', '""' )
                tvg = str( channel.get( 'tvg_id', '' ) or '' ).replace( '"', '""' )

                # print the comma delimited row
                print( f'"{name}","{tvg}"' )

        # whoopsie...
        except Exception as e:
            print( f"Error in export_channels: {str(e)}" )
            raise

    # get all the epg data records
    def _get_epg_data( self ) -> List[Dict[str, Any]]:

        # let's give it a shot
        try:

            # hold the response
            response = requests.get(
                f"{self.base_url}/api/epg/epgdata/?page_size=2500",
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # hold the data
            data = response.json( )

            # if the response is paginated, return the results, otherwise it's already a list
            return data['results'] if isinstance( data, dict ) else data

        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Failed to fetch EPG data" )

    # get all the m3u accounts
    def _get_m3u_accounts( self ) -> List[Dict[str, Any]]:

        # let's give it a shot
        try:

            # hold the response
            response = requests.get(
                f"{self.base_url}/api/m3u/accounts/",
                headers=self.auth_headers,
                timeout=30
            )

            # make sure we're setup to throw an actual error on an error status
            response.raise_for_status( )

            # hold the data
            data = response.json( )

            # if the response is paginated, return the results, otherwise it's already a list
            return data['results'] if isinstance( data, dict ) else data

        # whoopsie...
        except requests.exceptions.RequestException as e:
            self._exception( e, "Failed to fetch M3U accounts" )

    # match channel tvg-ids to their mapped epg data tvg-ids
    def match_epg( self ) -> None:

        # give it a shot
        try:

            # grab all existing channels
            print( "Fetching channels..." )
            channels = self._get_channels( )
            print( f"Found {len(channels)} channels" )

            # grab all the epg data and map it by id
            print( "Fetching EPG data..." )
            epg_map = { epg['id']: epg.get( 'tvg_id' ) for epg in self._get_epg_data( ) }
            print( f"Found {len(epg_map)} EPG records" )

            # hold the update count
            updated = 0

            # loop over the channels
            for channel in channels:

                # grab the mapped epg tvg-id if there is one
                epg_tvg_id = epg_map.get( channel.get( 'epg_data_id' ) )

                # skip if there's no mapping, no epg tvg-id, or it already matches
                if not epg_tvg_id or channel.get( 'tvg_id' ) == epg_tvg_id:
                    continue

                # patch the channels tvg-id
                response = requests.patch(
                    f"{self.base_url}/api/channels/channels/{channel['id']}/",
                    json={ 'tvg_id': epg_tvg_id },
                    headers=self.auth_headers,
                    timeout=30
                )

                # make sure we're setup to throw an actual error on an error status
                response.raise_for_status( )

                # log/print the update
                print( f"Updated {channel.get( 'name' )}: {channel.get( 'tvg_id' )} -> {epg_tvg_id}" )
                updated += 1

            # log/print the total
            print( f"{updated} Channels Updated" )

        # whoopsie...
        except Exception as e:
            print( f"Error in match_epg: {str(e)}" )
            raise

    # renumber the channels sequentially by name
    def renumber_channels( self ) -> None:

        # give it a shot
        try:

            # grab all existing channels
            print( "Fetching channels..." )
            channels = self._get_channels( )
            print( f"Found {len(channels)} channels" )

            # sort them by their name
            channels = sorted( channels, key=lambda c: str( c.get( 'name', '' ) ).lower( ) )

            # hold the update count
            updated = 0

            # loop over the channels, numbering them sequentially
            for number, channel in enumerate( channels, start=1 ):

                # skip it if it's already numbered correctly
                if channel.get( 'channel_number' ) == number:
                    continue

                # patch the channels number
                response = requests.patch(
                    f"{self.base_url}/api/channels/channels/{channel['id']}/",
                    json={ 'channel_number': number },
                    headers=self.auth_headers,
                    timeout=30
                )

                # make sure we're setup to throw an actual error on an error status
                response.raise_for_status( )

                # log/print the update
                print( f"Renumbered {channel.get( 'name' )}: {channel.get( 'channel_number' )} -> {number}" )
                updated += 1

            # log/print the total
            print( f"{updated} Channels Renumbered" )

        # whoopsie...
        except Exception as e:
            print( f"Error in renumber_channels: {str(e)}" )
            raise

    # reorder each channels streams by their m3u account name
    def reorder_streams( self ) -> None:

        # give it a shot
        try:

            # grab all existing channels
            print( "Fetching channels..." )
            channels = self._get_channels( )
            print( f"Found {len(channels)} channels" )

            # grab all the m3u accounts and map their names by id
            print( "Fetching M3U accounts..." )
            m3u_names = { account['id']: str( account.get( 'name', '' ) ) for account in self._get_m3u_accounts( ) if isinstance( account, dict ) and 'id' in account }
            print( f"Found {len(m3u_names)} M3U accounts" )

            # grab all streams and map their sort keys by id
            print( "Fetching streams..." )
            stream_keys = {
                stream['id']: (
                    m3u_names.get( stream.get( 'm3u_account' ), '' ).lower( ),
                    str( stream.get( 'name', '' ) ).lower( )
                )
                for stream in self._get_streams( )
                if isinstance( stream, dict ) and 'id' in stream
            }
            print( f"Found {len(stream_keys)} streams" )

            # hold the update count
            updated = 0

            # loop over the channels
            for channel in channels:

                # hold the current stream ids
                current = channel.get( 'streams' ) or []

                # nothing to reorder here
                if len( current ) < 2:
                    continue

                # sort the ids by their m3u account name, then their stream name
                ordered = sorted( current, key=lambda sid: stream_keys.get( sid, ( '', '' ) ) )

                # already in order, move along
                if ordered == current:
                    continue

                # patch the channels stream order
                response = requests.patch(
                    f"{self.base_url}/api/channels/channels/{channel['id']}/",
                    json={ 'streams': ordered },
                    headers=self.auth_headers,
                    timeout=30
                )

                # make sure we're setup to throw an actual error on an error status
                response.raise_for_status( )

                # log/print the update
                print( f"Reordered {channel.get( 'name' )}: {len(ordered)} Streams" )
                updated += 1

            # log/print the total
            print( f"{updated} Channels Reordered" )

        # whoopsie...
        except Exception as e:
            print( f"Error in reorder_streams: {str(e)}" )
            raise