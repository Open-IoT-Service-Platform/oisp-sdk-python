# Copyright (c) 2015, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Intel Corporation nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""@package Account
Methods for IoT Analytics account management
"""
from device import Device


class Account(object): #TODO document attributes

    """ Create IoT Account instance

    """

    ROLE_ADMIN="admin"

    def __init__(self, name, account_id, role, client):
        self.name = name
        self.account_id = account_id
        self.role = role
        self.client = client
        self.devices = None
        self.activation_code = None
        self.activation_code_valid_until = None

    def __str__(self):
        return "Account | name: {}\tid:{}\trole:{}".format(self.name,
                                                           self.account_id,
                                                           self.role)


    def delete(self):
        """ Delete account"""
        resp = self.client._delete("/accounts/{}".format(self.account_id))
        assert resp.status_code == 204 #TODO inform client


    def get_activation_code(self, auto_refresh=True):
        """ Return previous activation code a string if it is still valid.

        If auto_refresh is True (default), this will automatically
        request a new activation code if the old one is expired.
        Otherwise it will return None
        """
        endpoint = "/accounts/{}/activationcode".format(self.account_id)
        resp = self.client._get(endpoint)
        assert resp.status_code == 200, "Could not get activation code" #TODO proper exception
        activation_code = resp.json()["activationCode"]
        time_left = resp.json()["timeLeft"]
        if not activation_code and auto_refresh:
            activation_code = self.refresh_activation_code()
        self.activation_code = activation_code
        self.activation_code_valid_until = None #TODO check for validation
        return activation_code


    def refresh_activation_code(self): #TODO document
        endpoint = "/accounts/{}/activationcode/refresh".format(self.account_id)
        resp = self.client._put(endpoint)
        assert resp.status_code==200, "Error while refreshing activation code" #TODO proper exception
        self.activation_code = resp.json()["activationCode"]
        return self.activation_code


    def get_devices(self): # TODO Documentation
        endpoint = "/accounts/{}/devices".format(self.account_id)
        resp = self.client._get(endpoint)
        assert resp.status_code == 200, "Could not retrieve devices" #TODO proper exception
        devices = [] # TODO decide whether old devices should be kept
        for device_json in resp.json():
            devices.append(Device(account=self,
                                  device_id=device_json.get("deviceId"), #TODO from_json method
                                  name=device_json.get("name"),
                                  gateway_id=device_json.get("gatewayId"),
                                  domain_id=device_json.get("domainId"),
                                  created_on=device_json.get("created")))
        self.devices = devices
        return devices


    def create_device(self, device_id, name, gateway_id=None, tags=[], loc=None,
                      attributes=None): #TODO Documentation
        endpoint = "/accounts/{}/devices".format(self.account_id)
        if gateway_id is None:
            gateway_id = device_id
        payload = {"deviceId": device_id, "gatewayId": gateway_id, "name":name}
        if tags:
            payload["tags"] = tags
        if loc:
            payload["loc"] = loc
        if attributes:
            payload["attributes"] = attributes
        resp = self.client._post(endpoint, data=payload)
        assert resp.status_code == 201, "Device creation failed" #TODO proper exceptions

        return Device(account=self, device_id=resp.json().get("deviceId"), #TODO from_json method
                      name=resp.json().get("name"),
                      gateway_id=resp.json().get("gatewayId"),
                      domain_id=resp.json().get("domainId"),
                      created_on=resp.json().get("created"))


    def get_component_types(self): #TODO OOP
        endpoint = "/accounts/{}/cmpcatalog?full=true".format(self.account_id)
        return self.client._get(endpoint)
