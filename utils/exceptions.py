from typing import Optional

# setup the exception class
class APIException( Exception ):
    
    # setup the class with the defaults messages, status codes, and responses
    def __init__( self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None ):
        
        # if we have a status code and text from the API
        if status_code is not None and response_text is not None:

            # setup the actual message we're going to show
            message = f"{message}: {status_code} - {response_text}"

        # DO IT!!!
        super( ).__init__( message )
        