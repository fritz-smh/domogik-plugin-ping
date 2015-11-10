# -*- coding: utf-8 -*- 

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Ping ip devices

Implements
==========

class Ping
class Nmap to detect alive hosts

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time
import traceback
#from threading import Event
import subprocess
from domogik.common.utils import get_ip_for_interfaces

try:
    import nmap
except:
    print("python-nmap is not installed")



class Ping:
    """
    """

    def __init__(self, log, address, interval, callback, stop):
        """
        Ping a device each n seconds
        @param log : log instance
        @param address : ip or address to ping
        @param interval : interval between each data sent
        @param callback : callback to return values
        @param stop : threading.Event instance
        """
        self.log = log
        self.address = address
        self.interval = interval
        self.callback = callback
        self._stop = stop
        self.start_ping()

    def start_ping(self):
        """ 
        Start pinging
        """
        while not self._stop.isSet():
            cmd = "ping -c 1 {0}".format(self.address)
            ret = subprocess.call(cmd, shell = True)
            xpl_type = "xpl-stat"
            if ret == 0:
                self.log.debug(u"{0} is alive".format(self.address))
                self.callback(xpl_type, {"type" : "input", "device" : self.address, "current" : "high"})
            else:
                self.log.debug(u"{0} is NOT alive".format(self.address))
                self.callback(xpl_type, {"type" : "input", "device" : self.address, "current" : "low"})
            self.log.debug(u"{0} : wait for {1} seconds".format(self.address, self.interval))
            time.sleep(self.interval)


class Nmap:

    def __init__(self, log, cb_device_detected, stop):
        self.log = log
        self.cb_device_detected = cb_device_detected
        self._stop = stop
 
        try:
            self.nm = nmap.PortScanner()
        except:
            self.nm = None
            self.log.warning(u"Unable to create nmap port scanner. Please check that the package python-nmap is installed. IP devices autodetection will be skipped!")
        self.scan()

    def scan(self):
        if self.nm != None:
            while not self._stop.isSet():
                self.log.debug(u"Result of nmap scan: ")
                for int_ip in get_ip_for_interfaces():
                    try:
                        the_ip_tab = int_ip.split(".")
                        if the_ip_tab[0] == "127":
                            continue
                        the_ip = "{0}.{1}.{2}.0".format(the_ip_tab[0], the_ip_tab[1], the_ip_tab[2])
                        result = self.nm.scan(hosts='{0}/24'.format(the_ip), arguments='-n -sP')
                        for host in result['scan']:
                            status = result['scan'][host]['status']['state']
                            self.log.debug(u"{0} is {1}".format(host, status))
                            try:
                                ipv4 = result['scan'][host]['addresses']['ipv4']
                                self.log.debug(u"- ipv4 : {0}".format(ipv4))
                            except KeyError:
                                pass
                            try:
                                vendor = result['scan'][host]['vendor']
                                self.log.debug(u"- vendor : {0}".format(vendor))
                            except KeyError:
                                pass
    
                            self.cb_device_detected({
                                "device_type" : "ping.ping",
                                "reference" : "",
                                "global" : [],
                                "xpl" : [
                                    {
                                        "key" : "device",
                                        "value" : host
                                    }
                                ],
                                "xpl_commands" : {},
                                "xpl_stats" : {}
                            })
                    except KeyError:
                        # surely a nmap error :)
                        # skipping for this turn
                        self.log.warning(u"Nmap : no result for the scan...")
                        pass
    
                # sleep for 5 minutes
                time.sleep(5 * 60)
    
