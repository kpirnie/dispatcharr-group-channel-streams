import os
import configparser
from typing import Tuple, Optional

# global for the config file
CONFIG_FILE = ".dgcs_conf"

# read the config file
def read_config( ) -> Tuple[str, str, str]:
    
    # setup the config reader
    config = configparser.ConfigParser( )

    # if the file does not exist, return none
    if not os.path.exists( CONFIG_FILE ):
        return None, None, None
    
    # read the file
    config.read( CONFIG_FILE )

    # setup the returnable data, from the default profile
    endpoint = config.get( 'DEFAULT', 'API_ENDPOINT', fallback=None )
    username = config.get( 'DEFAULT', 'API_USER', fallback=None )
    password = config.get( 'DEFAULT', 'API_PASS', fallback=None )

    # return the config data
    return endpoint, username, password

# write the config
def write_config( endpoint: str, username: str, password: str ) -> None:
    
    # setup the config parser
    config = configparser.ConfigParser( )

    # and the default config profile
    config['DEFAULT'] = {
        'API_ENDPOINT': endpoint,
        'API_USER': username,
        'API_PASS': password
    }

    # open the file for writing
    with open( CONFIG_FILE, 'w' ) as configfile:
        
        # write the config
        config.write( configfile )

# prompt to get the input for the config
def prompt_for_config( overwrite: bool = False ) -> Tuple[str, str, str]:
    
    # setup the input requests
    print( "Please enter the following info..." )
    endpoint = input( "Dispatcharr URL [http(s)://HOST:PORT]: " ).strip( )
    username = input( "Username: " ).strip( )
    password = input( "Password: " ).strip( )
    
    # check if we're set to overwrit the existing config
    if overwrite or not os.path.exists( CONFIG_FILE ):

        # we are, so write it out
        write_config( endpoint, username, password )
        print( f"Configuration saved to {CONFIG_FILE}" )
    
    # return the config
    return endpoint, username, password

# get the config
def get_config( use_args: Optional[Tuple[str, str, str]] = None ) -> Tuple[str, str, str]:
    
    # If args provided, use them and save to config
    if use_args and all( use_args ):

        # setup the config frm the arguments
        endpoint, username, password = use_args

        # write them to the config file
        write_config( endpoint, username, password )

        # return the config
        return endpoint, username, password
    
    # Try to read from config file
    endpoint, username, password = read_config( )
    
    # if they're all there
    if all( [endpoint, username, password] ):
        
        # return the config
        return endpoint, username, password
    
    # Prompt user for config if we made it this far
    return prompt_for_config( )
