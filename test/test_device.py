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

from test.basecase import BaseCaseWithAccount

from oisp import Device, OICException


class DeviceTestCase(BaseCaseWithAccount):

    def test_activate_device(self):
        device = self.account.create_device("device_id", "device_name")
        self.assertEqual(device.status, Device.STATUS_CREATED)
        device.activate()
        # Get device again to update properities
        device = self.account.get_device(device.device_id)
        self.assertEqual(device.status, Device.STATUS_ACTIVE)

    def test_delete_device(self):
        device = self.account.create_device("device_id", "device_name")
        self.assertEqual(len(self.account.get_devices()), 1)
        device.delete()
        self.assertEqual(len(self.account.get_devices()), 0)

        can_delete_twice = True
        try:
            # Now it should fail
            device.delete()
        except OICException as e:
            self.assertEqual(e.code, 1404)
            can_delete_twice = False

        self.assertFalse(can_delete_twice)

    def test_attributes_tags_loc(self):
        attr = {"OS": "linux", "color": "blue"}
        device = self.account.create_device("device_id", "device_name",
                                            attributes=attr,
                                            tags=["testtag0", "testtag1"],
                                            loc=[0, 0])
        self.assertDictEqual(attr, device.attributes)
        attr["color"] = "red"
        device.set_properties(attributes=attr)
        self.assertDictEqual(attr, device.attributes)
        device.update()
        self.assertDictEqual(attr, device.attributes)
        self.assertCountEqual(["testtag0", "testtag1"], device.tags)
        self.assertEqual([0, 0], device.loc)

    def test_add_remove_component(self):
        device = self.account.create_device("device_id", "device_name")
        device.activate()
        resp = device.add_component("temp1", "temperature.v1.0")
        # method does not update components automatically
        device_updated = self.account.get_device("device_id")
        self.assertEqual(len(device_updated.components), 1)
        device_updated.delete_component(resp["cid"])
        self.assertEqual(device_updated.components, [])

    def test_device_from_token(self):
        device0 = self.account.create_device("device_tsft", "device_tsft")
        d_id = device0.device_id
        token = device0.activate()
        device1 = self.client.get_device(token, d_id)
        self.assertEqual(device0, device1)

    def test_set_props_update(self):
        device0 = self.account.create_device("device_tsft", "device_tsft")
        d_id = device0.device_id
        token = device0.activate()
        device1 = self.client.get_device(token, d_id)
        device0.add_component("temp1", "temperature.v1.0")
        test_attributes = {"test_attribute": "test_value"}
        device0.set_properties(attributes=test_attributes)

        # We also need to update device0, because it contains undetailed
        # information otherwise, != information in updated device1
        device0.update()
        device1.update()

        self.assertCountEqual(device0.components, device1.components)
        self.assertCountEqual(device1.attributes, test_attributes)

    def test_submit_data_with_device_token(self):
        device = self.account.create_device("device_id", "device_name")
        token = device.activate()
        device = self.client.get_device(token, device.device_id)
        resp = device.add_component("temp1", "temperature.v1.0")
        cid = resp["cid"]
        device.add_sample(cid, 10)
        device.submit_data()

    def test_submit_data_with_user_token(self):
        device = self.account.create_device("device_id", "device_name")
        device.activate()
        resp = device.add_component("temp1", "temperature.v1.0")
        cid = resp["cid"]

        # Refind device to lose device token
        for d in self.account.get_devices():
            if d.device_id == "device_id":
                device = d
                break

        device.add_sample(cid, 10)
        try:
            device.submit_data()
        except Warning:
            return

        raise Exception("submit_data with user token should fail [6th Apr 18]")

    def test_submit_binary_data(self):
        self.account.create_component_type("image", "1.0", "sensor",
                                           "ByteArray", "boolean", "pixel",
                                           "binaryDataRenderer")
        device = self.account.create_device("device_id", "device_name")
        device.activate()
        resp = device.add_component("temp1", "image.v1.0")
        cid = resp["cid"]

        data = bytes([1, 2, 3, 4])
        device.add_sample(cid, data)
        device.submit_data()

    def test_submit_boolean_data(self):
        self.account.create_component_type("bool", "1.0", "sensor",
                                           "Boolean", "boolean", "bool",
                                           "timeSeries")
        device = self.account.create_device("device_id", "device_name")
        device.activate()
        cid = device.add_component("bool1", "bool.v1.0")["cid"]
        # TODO this is bad, but needs fix in frontend
        device.add_sample(cid, "1")
        device.submit_data()
