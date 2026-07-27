import argparse

# setup the argument class
class Args:

    # parse the arguments
    def parse_args( ):

        # hold the parser
        parser = argparse.ArgumentParser( description='Dispatcharr Channel Stream Grouper' )
        parser.add_argument( '--endpoint', help='API endpoint URL' )
        parser.add_argument( '--username', help='API username' )
        parser.add_argument( '--password', help='API password' )
        parser.add_argument( '--normalizer', help='RegExp to normalize channel names', default=None )
        parser.add_argument( '--refresh', action='store_true', help='Force a full M3U refresh' )
        parser.add_argument( '--reconfigure', action='store_true',  help='Force reconfiguration and overwrite existing config' )
        parser.add_argument( '--prune', action='store_true', help='Remove stale streams from grouped channels' )
        parser.add_argument( '--export', action='store_true', help='Export channel names and tvg-ids to stdout' )
        parser.add_argument( '--match-epg', action='store_true', help='Update channel tvg-ids from their mapped EPG data' )
        parser.add_argument( '--renumber', action='store_true', help='Channel renumbering' )
        parser.add_argument( '--reorder-streams', action='store_true', help='Reorder each channels streams by stream name' )

        # return the parsed arguments
        return parser.parse_args( )
    