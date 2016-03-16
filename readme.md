# Presencify

## Overview

Short version: I spent hours trying to get presence detection using OpenHAB network health binding, persistence bindings and complex rules working. It's amazing how complicated that is and how bad it is working. I gave up, took three hours and wrote this little python program instead. It's working like a charm for me! :)

## Installation

### OpenHAB

Make sure you have configured atleast one item corresponding to the device you want to monitor. If you have more than one device that should be controlling the same presence then add them to a group, create another switch for "Presence" and add the following little rule:

```javascript
rule "Presence update"
when
        Item Mobiles changed
then
        if (Presence.state != ON) {
                if (Mobiles.members.filter(s | s.state == ON).size > 0) {
                        sendCommand(Presence, ON)
                }
        }
        else {
                if (Mobiles.members.filter(s | s.state == ON).size == 0) {
                        sendCommand(Presence, OFF)
                }
        }
end
```

### Presencify

Copy default.conf to presencify.conf. Open it and change the three configuration items for ip addresses, item names and openhab rest url. Start the script and enjoy! :)

## How it works

The script runs continuously and pings all devices each 5 seconds. If the device responds on any of 3 pings within 3 seconds the device state will be updated in OpenHAB to "ON", if it was "OFF" before. If the ping fails however, then the state won't be updated to "OFF" until it has been failing all the pings for 5 minutes in a row. This solves a lot of problems with phones being in power save mode. All the mentioned intervals/timeouts are configurable.

## Contributors

Feel free to give feedback or merge requests!

## License

Code relased under [the MIT license](https://github.com/twbs/bootstrap/blob/master/LICENSE)
