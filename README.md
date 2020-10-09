# Synchronize Snapcast clients to MPD outputs

This script synchronized the muted state of [Snapcast] clients to the enabled
state of [MPD] outputs.

Since MPD itself cannot currently speak the Snapcast protocol, I use this to
control where the MPD output is supposed to be played (in terms of Snapcast
clients) from the MPD client app while still having the advantages of
synchronized playback thanks to Snapcast.

[Snapcast]: https://github.com/badaix/snapcast
[MPD]: https://www.musicpd.org/

## Setup

The script expects the name of the Snapcast client to match the name of the MPD
output. So for example, if you have a Snapcast client named "Living Room", put
the following into your `mpd.conf`:

```
audio_output {
        type            "null"
        name            "Living Room"
}
```

After restarting MPD, you will have an output named "Living Room" in your MPD
client app. When you toggle it, this script will change the muted state of the
Snapcast client of the same name, and vice versa.

If you have multiple Snapcast clients with the same name as the MPD output,
behavior is undefined.

## Usage

```
usage: main.py [-h] [-s SNAPCAST_SERVER] [-m MPD_SERVER] [-l LOGLEVEL]

optional arguments:
  -h, --help            show this help message and exit
  -s SNAPCAST_SERVER, --snapcast-server SNAPCAST_SERVER
                        'localhost'
  -m MPD_SERVER, --mpd-server MPD_SERVER
                        'localhost'
  -l LOGLEVEL, --loglevel LOGLEVEL
                        'INFO'
```
