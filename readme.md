# Dispatcharr Group Channel Streams

## Instructions

* fire up terminal and `cd` into the directory you wish to be in
* Clone the repo: `git clone https://gitlab.com/kp-development/python/dispatcharr-group-channel-streams.git`
* `cd` into the repo's directory.
* type in: `python3 main.py`
* The app will prompt you for the rest, or run it with the arguments below

### App Arguments

**These arguments do not need any values.**

* `--reconfigure`: Add to prompt you to reconfigure the app
* `--refresh`: Add to refresh all M3Us you have associated with your account in your Dispatcharr instance

**These arguments require values.**

* `--endpoint SCHEMA:HOST:PORT`: (required) The schema, host, and port to your Dispatcharr instance; ex: http://127.0.0.1:1234
* `--username STRING`: (required) The username of the Dispatcharr account you want to attach to.
* `--password STRING`: (required) The password of the Dispatcharr account you want to attach to.
* `--normalizer REGEXP STRING`: The regular expression(s) for strings you want to remove from the channel names. For example say you have channels that are suffixed with HD or SD, if you want them off the names, you would use a string like: "\sHD|\sSD".  Make sure to wrap them in quotes.
