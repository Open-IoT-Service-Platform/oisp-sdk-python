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

from iotkitclient import Device, OICException


class DeviceTestCase(BaseCaseWithAccount):

    def test_activate_device(self):
        device = self.account.create_device("device_id", "device_name")
        self.assertEqual(device.status, Device.STATUS_CREATED)
        token = device.activate()
        # Get device again to update properities
        device = self.account.get_device(device.device_id)
        self.assertEqual(device.status, Device.STATUS_ACTIVE)

    def test_delete_device(self):
        device = self.account.create_device("device_id", "device_name")
        self.assertEqual(len(self.account.get_devices()), 1)
        device.delete()
        self.assertEqual(len(self.account.get_devices()), 0)

        try:
            # Now it should fail
            device.delete()
            can_delete_twice = True
        except OICException as e:
            self.assertEqual(e.code, 1404)
            can_delete_twice = False

        self.assertFalse(can_delete_twice)

    def test_add_remove_component(self):
        device = self.account.create_device("device_id", "device_name")
        token = device.activate()
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
