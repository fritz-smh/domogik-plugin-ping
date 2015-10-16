#!/usr/bin/python
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

Get informations about one wire network

Implements
==========

Ping feature

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik_packages.plugin_ping.lib.ping import Ping, Nmap
import time
import threading
import traceback


class PingManager(XplPlugin):

    def __init__(self):
        """ Init 
        """
        XplPlugin.__init__(self, name='ping')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        ### get the devices list
        # for this plugin, if no devices are created we won't be able to use devices.
        # but.... if we stop the plugin right now, we won't be able to detect existing device and send events about them
        # so we don't stop the plugin if no devices are created
        self.devices = self.get_device_list(quit_if_no_device = False)

        ### get all config keys
        # n/a

        ### For each device
        threads = {}
        for a_device in self.devices:
            try:
                interval = self.get_parameter(a_device, "interval")
                address = self.get_parameter_for_feature(a_device, "xpl_stats", "ping", "device")
                self.log.info("Launch thread to ping {0}. Address = {1}, interval = {2} seconds".format(a_device["name"], address, interval))
                thr_name = "{0}".format(a_device['name'])
                threads[thr_name] = threading.Thread(None, 
                                           Ping,
                                           thr_name,
                                           (self.log,
                                            address, 
                                            interval,
                                            self.send_xpl,
                                            self.get_stop()),
                                           {})
                threads[thr_name].start()
                self.register_thread(threads[thr_name])
            except:
                self.log.error(u"{0}".format(traceback.format_exc()))

        ### Devices autodetection with nmap
        try:
            self.log.info("Launch thread For devices autodetection")
            thr_nmap = threading.Thread(None, 
                                       Nmap,
                                       "nmap",
                                       (self.log,
                                        self.device_detected,
                                        self.get_stop()),
                                       {})
            thr_nmap.start()
            self.register_thread(thr_nmap)
        except:
            self.log.error(u"{0}".format(traceback.format_exc()))

        # notify ready
        self.ready()

    def send_xpl(self, type, data):
        """ Send data on xPL network
            @param data : data to send (dict)
        """
        msg = XplMessage()
        msg.set_type(type)
        msg.set_schema("sensor.basic")
        for element in data:
            msg.add_data({element : data[element]})
        self.log.debug("Send xpl message...")
        self.log.debug(msg)
        self.myxpl.send(msg)


if __name__ == "__main__":
    p = PingManager()
