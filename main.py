# default imports
from config.config_handler import get_config, prompt_for_config
from utils.args import Args
from api.dchg_main import DCHG_Main
import sys

# our graceful exitter
def graceful_exit( signum, frame ):
    
    # exit the app and processes
    print( "\nOperation cancelled by user. Exiting..." )
    sys.exit( 0 )

# our main program
def main( ):

    # Register the signal handlers for graceful exit
    import signal
    signal.signal( signal.SIGINT, graceful_exit )  # CTRL-C
    signal.signal( signal.SIGTERM, graceful_exit )  # Termination signal

    # pull in and parse the arguments
    args = Args.parse_args( )
    
    # let's give it a shot
    try:

        # are we reconfiguring?
        if args.reconfigure:

            # we are, so make sure we are setting up what we need for it
            endpoint, username, password = prompt_for_config( overwrite=True )
        
        # nope
        else:

            # grab the config, either from the saved file, or the arguments passed
            endpoint, username, password = get_config(
                use_args = ( args.endpoint, args.username, args.password ) if any( [args.endpoint, args.username, args.password] ) else None
            )

        # looks like we're missing something...
        if not all( [endpoint, username, password] ):
            raise ValueError( "Missing required configuration parameters" )

        # initialize the main class
        api = DCHG_Main( endpoint, username, password )
        print( "Starting channel creation..." )
        
        # create/update the channels
        results = api.create_channels( )
        print( f"Successfully processed {len(results)} channels" )

    # somebody doesn't want to run...
    except KeyboardInterrupt:

        # toss a message out and exit
        print( "\nOperation cancelled by user. Exiting..." )
        sys.exit( 0 )

    # whoopsie...
    except Exception as e:

        # throw a fatal error and make sure we kill the app
        print( f"Fatal error: {str(e)}" )
        raise

# Run the app!
if __name__ == "__main__":
    main( )
    