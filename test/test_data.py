# Copyright (c) 2017-2019, Intel Corporation
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
import time

from test.basecase import BaseCaseWithAccount
from oisp import DataQuery

# Time to wait until the data is written to storage
# This is an unrealistic large value to allow testing
# clusters on low resource machines
DATA_WRITE_WAIT = 5


class DataTestCase(BaseCaseWithAccount):

    def setUp(self):
        BaseCaseWithAccount.setUp(self)
        self.account.create_component_type("image", "1.0", "sensor",
                                           "ByteArray", "boolean", "pixel",
                                           "binaryDataRenderer")

        self.account.create_component_type("bool", "1.0", "sensor",
                                           "Boolean", "boolean", "bool",
                                           "timeSeries")

        self.device = self.account.create_device("device_id", "device_name")
        self.device.activate()
        self.cid = {}
        self.cid["temp"] = self.device.add_component("temp",
                                                     "temperature.v1.0")["cid"]
        self.cid["img"] = self.device.add_component("img1",
                                                    "image.v1.0")["cid"]
        self.cid["bool"] = self.device.add_component("bool1",
                                                     "bool.v1.0")["cid"]

    def test_get_submitted_data(self):
        self.device.add_sample(self.cid["temp"], 10)
        self.device.submit_data()
        time.sleep(DATA_WRITE_WAIT)
        data = self.account.search_data(DataQuery())
        self.assertEqual(len(data.samples), 1)
        # As this test was written, the platform returned strings
        # for every data type, hence "10"
        self.assertCountEqual([s.value for s in data.samples], [10])

    def test_get_multiple_samples(self):
        self.device.add_sample(self.cid["temp"], 10)
        # We have to wait shortly, otherwise, samples have the same timestamp
        # and OISP ignores one of the samples. See
        # https://github.com/Open-IoT-Service-Platform/oisp-frontend/issues/161
        self.device.add_sample(self.cid["bool"], True)
        self.device.submit_data()
        time.sleep(DATA_WRITE_WAIT)
        data = self.account.search_data(DataQuery())
        self.assertEqual(len(data.samples), 2)
        # As this test was written, the platform returned strings
        # for every data type, hence "10" and "20"
        self.assertCountEqual([s.value for s in data.samples], [10, True])

    def test_get_multiple_samples_from_multiple_components(self):
        self.device.add_sample(self.cid["temp"], 10)
        # TODO bad ("1") but must be fixed at frontend
        self.device.add_sample(self.cid["bool"], True)
        self.device.submit_data()
        time.sleep(DATA_WRITE_WAIT)
        data = self.account.search_data(DataQuery())
        self.assertEqual(len(data.samples), 2)
        # As this test was written, the platform returned strings
        # for every data type, hence "10" and "20"
        self.assertCountEqual([s.value for s in data.samples], [10, True])

    def test_get_submitted_binary_data(self):
        BINARY_PAYLOAD = bytes([1, 2, 3, 4, 5, 6])
        self.device.add_sample(self.cid["img"], BINARY_PAYLOAD)
        self.device.submit_data()
        time.sleep(DATA_WRITE_WAIT)
        data = self.account.search_data(DataQuery())
        self.assertEqual(len(data.samples), 1)
        self.assertEqual(data.samples[0].value, BINARY_PAYLOAD)
