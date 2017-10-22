#!/usr/bin/python

import time
import requests
import os
import ConfigParser
import sys

class Presencify:
    def __init__(self, ip_macs, iphones, interval, fail_retries, fail_margin, initial_status, timeout, callback):
        self._ip_macs        = ip_macs
        self._iphones        = iphones
        self._interval       = interval
        self._fail_retries   = fail_retries
        self._fail_margin    = fail_margin
        self._initial_status = initial_status
        self._timeout        = timeout
        self._callback       = callback
        self._last_state     = {}

        self._init()

    def _init(self):
        for ip_address in self._ip_macs:
            self._last_state[ip_address] = { 'last_state': self._initial_status,
                                             'last_timestamp': 0 }

    def run(self):
        while True:
            # Go through ip addresses and ping them individually
            for ip_address in self._ip_macs:
                state = self._is_reachable(ip_address, self._fail_retries, self._timeout)

                print "[%s] State: %s, Last: %s, Timestamp: %d" % (ip_address,
                                                                   str(state),
                                                                   self._last_state[ip_address]['last_state'],
                                                                   self._last_state[ip_address]['last_timestamp'])

                if self._last_state[ip_address]['last_state'] != state:
                    # If new state is off and old state is on, make sure that old state is old enough
                    now_minus_margin = time.time() - self._fail_margin
                    if state or self._last_state[ip_address]['last_timestamp'] < now_minus_margin:
                        print "[%s] Signal state: %s" % (ip_address, str(state))
                        self._signal(ip_address, state)
                        self._last_state[ip_address]['last_state'] = state

                # Only update last timestamp if state is True. This makes sense
                # because we want to track the time of the latest ON->OFF transition
                # when we want to decide if should signal OFF. But an OFF->ON transition
                # should always trigger a signal no matter what.
                if state:
                    self._last_state[ip_address]['last_timestamp'] = time.time()

            # Sleep until next check
            time.sleep(self._interval)

    def _is_reachable(self, ip_address, fail_retries, timeout):
        # Check for up to {fail_retries} times
        for i in range(1, fail_retries):
            state = self._ping(ip_address, timeout)

            if state:
                return True

        return False

    def _ping(self, ip_address, timeout):
        if ip_address in self._iphones:
            print "hping3:ing and arping %s with mac %s and timeout %d" % (ip_address, self._ip_macs[ip_address], timeout)
            return os.system("./ping_iphone.sh %s %s" % (ip_address, self._ip_macs[ip_address])) == 0
        else:
            print "Pinging %s with timeout %d" % (ip_address, timeout)
            return os.system("ping -c 1 -t %d %s > /dev/null" % (timeout, ip_address)) == 0

    def _signal(self, ip_address, state):
        self._callback(ip_address, state)

class RestSignaler:
    def __init__(self, url, items):
        self._url   = url
        self._items = items

    def signal(self, ip_address, state):
        data = "ON" if state else "OFF"
        url = self._url + "/" + self._items[ip_address] + "/state"
        response = requests.put(url, data=data)
        if not response.ok:
            print "Error during REST update: " + response.content

if __name__ == '__main__':
    defaults = {'interval':       '5',
                'fail_retries':   '3',
                'fail_margin':    '300',
                'initial_status': 'False',
                'timeout':        '3'}

    config = ConfigParser.ConfigParser(defaults)

    config.read("presencify.conf")

    ip_addresses  = None
    mac_addresses = None
    items         = None
    rest_url      = None

    try:
        ip_addresses  = config.get("presencify", "ip_addresses").split(',')
        mac_addresses = config.get("presencify", "mac_addresses").split(',')
        iphones       = config.get("presencify", "iphones").split(',')
        item_list     = config.get("presencify", "items").split(',')
        rest_url      = config.get("presencify", "rest_url")

        items = dict(zip(ip_addresses, item_list))
        ip_macs = dict(zip(ip_addresses, mac_addresses))
    except Exception, e:
        print "Error reading config file. Missing required parameters?"
        sys.exit(1)

    rest_signaler = RestSignaler(rest_url, items)

    presencify = Presencify(ip_macs, iphones,
                            int(config.get("presencify", "interval")),
                            int(config.get("presencify", "fail_retries")),
                            int(config.get("presencify", "fail_margin")),
                            config.get("presencify", "initial_status") == 'True',
                            int(config.get("presencify", "timeout")),
                            rest_signaler.signal)
    presencify.run()
