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
        
        # return the parsed arguments
        return parser.parse_args( )
    