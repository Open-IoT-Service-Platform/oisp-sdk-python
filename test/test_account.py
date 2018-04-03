# Copyright (c) 2017, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of Intel Corporation nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
import test.config as config
from test.basecase import BaseCaseWithAccount


class GetCreateDeviceTestCase(BaseCaseWithAccount):

    def test_get_create_device(self):
        no_devices = self.account.get_devices()
        self.assertEqual(no_devices, [])
        device = self.account.create_device("device_id", "device_name")
        devices = self.account.get_devices()
        self.assertEqual(devices, [device])
        device_by_id = self.account.get_device(device.device_id)
        self.assertEqual(device_by_id, device)

    def test_component_catalog(self):
        example_ctype = {
            "id": "temperature.v2.0",
            "dimension": "temperature",
            "version": "2.0",
            "type": "sensor",
            "dataType": "Number",
            "format": "float",
            "min": "-150",
            "max": "150",
            "default": False,
            "measureunit": "Degrees Celsius",
            "display": "timeSeries"
        }
        self.account.create_component_type(dimension="temperature",
                                           version="2.0",
                                           ctype="sensor",
                                           data_type="Number",
                                           data_format="float",
                                           measure_unit="Degrees Celsius",
                                           display="timeSeries",
                                           min_val=-150,
                                           max_val=150)
        component_types = self.account.get_component_types_catalog(full=True)
        # Remove some for testing
        for ct in component_types:
            ct.pop("href")
            ct.pop("_id")
            ct.pop("domainId")
        self.assertTrue(example_ctype in component_types)

        self.account.update_component_type("temperature.v2.0", max_val=200)

        component_types = self.account.get_component_types_catalog(full=True)
        # Remove some for testing
        for ct in component_types:
            ct.pop("href")
            ct.pop("_id")
            ct.pop("domainId")

        example_ctype["id"] = "temperature.v2.1"
        example_ctype["version"] = "2.1"
        example_ctype["max"] = "200"

        self.assertTrue(example_ctype in component_types)
