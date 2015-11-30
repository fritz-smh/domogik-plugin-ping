#!/usr/bin/python
# -*- coding: utf-8 -*-

from domogik.xpl.common.plugin import XplPlugin
from domogik.tests.common.plugintestcase import PluginTestCase
from domogik.tests.common.testplugin import TestPlugin
from domogik.tests.common.testdevice import TestDevice
from domogik.tests.common.testsensor import TestSensor
from domogik.common.utils import get_sanitized_hostname
from datetime import datetime
import unittest
import sys
import os
import traceback

class PingTestCase(PluginTestCase):

    def test_0100_ping_on(self):
        """ check if all the xpl messages for a device up is sent
            Example : 
            xpl-trig : schema:sensor.basic, data:{'type': 'input', 'current': 'high', 'device': 127.0.00.1'}
        """
        global devices

        address = "127.0.0.1"

        # test 
        print(u"Device address = {0}".format(address))
        print(u"Device id = {0}".format(devices[address]))
        print(u"Check that a message with current = 'high' is sent.")
        
        self.assertTrue(self.wait_for_xpl(xpltype = "xpl-stat",
                                          xplschema = "sensor.basic",
                                          xplsource = "domogik-{0}.{1}".format(self.name, get_sanitized_hostname()),
                                          data = {"type" : "input",
                                                  "device" : address,
                                                  "current" : "high"},
                                          timeout = 10))
        print(u"Check that the value of the xPL message has been inserted in database")
        sensor = TestSensor(devices[address], "ping")
        print(sensor.get_last_value())
        from domogik_packages.plugin_ping.conversion.from_low_high_to_DT_Switch import from_low_high_to_DT_Switch
        # the data is converted to be inserted in database
        self.assertTrue(int(sensor.get_last_value()[1]) == from_low_high_to_DT_Switch(self.xpl_data.data['current']))


    def test_0101_ping_off(self):
        """ check if all the xpl messages for a device off is sent
            Example : 
            xpl-trig : schema:sensor.basic, data:{'type': 'input', 'current': 'low', 'device': 1.1.1.1'}
        """
        global devices

        address = "1.1.1.1"

        # test 
        print(u"Device address = {0}".format(address))
        print(u"Device id = {0}".format(devices[address]))
        print(u"Check that a message with current = 'low' is sent.")
        
        self.assertTrue(self.wait_for_xpl(xpltype = "xpl-stat",
                                          xplschema = "sensor.basic",
                                          xplsource = "domogik-{0}.{1}".format(self.name, get_sanitized_hostname()),
                                          data = {"type" : "input",
                                                  "device" : address,
                                                  "current" : "low"},
                                          timeout = 20))
        print(u"Check that the value of the xPL message has been inserted in database")
        sensor = TestSensor(devices[address], "ping")
        print(sensor.get_last_value())
        from domogik_packages.plugin_ping.conversion.from_low_high_to_DT_Switch import from_low_high_to_DT_Switch
        # the data is converted to be inserted in database
        print(int(sensor.get_last_value()[1]))
        print(from_low_high_to_DT_Switch(self.xpl_data.data['current']))
        self.assertTrue(int(sensor.get_last_value()[1]) == from_low_high_to_DT_Switch(self.xpl_data.data['current']))




if __name__ == "__main__":

    test_folder = os.path.dirname(os.path.realpath(__file__))

    ### global variables
    # the key will be the device address
    devices = {"127.0.0.1" : 0, 
               "1.1.1.1" : 0}

    ### configuration

    # set up the xpl features
    xpl_plugin = XplPlugin(name = 'test', 
                           daemonize = False, 
                           parser = None, 
                           nohub = True,
                           test  = True)

    # set up the plugin name
    name = "ping"

    # set up the configuration of the plugin
    # configuration is done in test_0010_configure_the_plugin with the cfg content
    # notice that the old configuration is deleted before
    cfg = { 'configured' : True}

    ### start tests

    # load the test devices class
    td = TestDevice()

    # delete existing devices for this plugin on this host
    client_id = "{0}-{1}.{2}".format("plugin", name, get_sanitized_hostname())
    try:
        td.del_devices_by_client(client_id)
    except: 
        print(u"Error while deleting all the test device for the client id '{0}' : {1}".format(client_id, traceback.format_exc()))
        sys.exit(1)

    # create a test device
    try:
        params = td.get_params(client_id, "ping.ping")
   
        for dev in devices:
            print("DEV={0}".format(dev))
            # fill in the params
            params["device_type"] = "ping.ping"
            params["name"] = "test_device_ping_{0}_é".format(dev)
            params["reference"] = "reference"
            params["description"] = "description"
            # global params
            pass # there are no global params for this plugin
            # xpl params
            # usually we configure the xpl parameters. In this device case, we can have multiple addresses
            # so the parameters are configured on xpl_stats level
            for the_param in params['global']:
                if the_param['key'] == "interval":
                    the_param['value'] = 10
            #for the_param in params['xpl_stats']['ping']:
            for the_param in params['xpl']:
                if the_param['key'] == "device":
                    the_param['value'] = dev
            # create
            device_id = td.create_device(params)['id']
            devices[dev] = device_id

    except:
        print(u"Error while creating the test devices : {0}".format(traceback.format_exc()))
        sys.exit(1)

    
    ### prepare and run the test suite
    suite = unittest.TestSuite()
    # check domogik is running, configure the plugin
    suite.addTest(PingTestCase("test_0001_domogik_is_running", xpl_plugin, name, cfg))
    suite.addTest(PingTestCase("test_0010_configure_the_plugin", xpl_plugin, name, cfg))
    
    # start the plugin
    suite.addTest(PingTestCase("test_0050_start_the_plugin", xpl_plugin, name, cfg))

    # do the specific plugin tests
    suite.addTest(PingTestCase("test_0100_ping_on", xpl_plugin, name, cfg))
    suite.addTest(PingTestCase("test_0101_ping_off", xpl_plugin, name, cfg))

    # do some tests comon to all the plugins
    #suite.addTest(PingTestCase("test_9900_hbeat", xpl_plugin, name, cfg))
    suite.addTest(PingTestCase("test_9990_stop_the_plugin", xpl_plugin, name, cfg))
    
    # quit
    res = unittest.TextTestRunner().run(suite)
    if res.wasSuccessful() == True:
        rc = 0   # tests are ok so the shell return code is 0
    else:
        rc = 1   # tests are ok so the shell return code is != 0
    xpl_plugin.force_leave(return_code = rc)


