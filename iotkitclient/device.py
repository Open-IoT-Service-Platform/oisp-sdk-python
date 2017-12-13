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

"""@package Device
Methods for IoT Analytics device management and data submission
"""
from datetime import datetime
import uuid

# pylint: disable=too-many-instance-attributes
# The attributes match those defined in the REST API
class Device(object):
    """ Class managing device activation, components, and attributes.

    To find or filter devices connected to an account, refer to the
    Account class."""

    # pylint: disable=too-many-arguments
    # Argument match attributes as defined in the REST API
    def __init__(self, account, device_id, name, gateway_id, domain_id,
                 created_on): #TODO include status
        self.account = account
        self.client = self.account.client
        self.device_id = device_id
        self.name = name
        self.gateway_id = gateway_id
        self.domain_id = domain_id
        if not isinstance(created_on, datetime):
            created_on = datetime.fromtimestamp(created_on / 1e3)
        self.created_on = created_on
        self.device_url = "/accounts/{}/devices/{}".format(account.account_id,
                                                           device_id)

    @staticmethod
    def from_json(account, json_dict):
        """ Create an device object using a json_dicton as returned
        by the host."""
        return Device(account=account,
                      device_id=json_dict.get("deviceId"), name=json_dict.get("name"),
                      gateway_id=json_dict.get("gatewayId"),
                      domain_id=json_dict.get("domainId"),
                      created_on=json_dict.get("created"))


    def delete(self):
        """ Delete device"""
        self.client.delete(self.device_url, expect=204)


    def activate(self):
        """ Activate device """
        endpoint = self.device_url + "/activation"
        payload = {"activationCode": self.account.get_activation_code()} #TODO try to use cache
        self.client.put(endpoint, data=payload, expect=200)


    # pylint: disable=unused-argument
    # The arguments are accesses through locals()
    def update(self, gateway_id=None, name=None, loc=None, tags=None,
               attributes=None): #TODO reconsider naming
        """ Change device properities """
        payload = {k:v for k, v in locals().items() if k != "self" and v}
        self.client.put(self.device_url, data=payload, expect=200)
        self.__dict__.update(payload) # TODO consider updating all


    def add_component(self, name, component_type, cid=None):
        """ Add a new component to the device

        Args
        ----------
        name: Component name
        component_type: Component type as listed in Component Catalog
        cid: Unique component id. If None specified, a UUID will be
        generated. """
        endpoint = self.device_url + "/components"
        if not cid:
            cid = str(uuid.uuid4())
        payload = {"cid":cid, "name":name, "type":component_type}
        resp = self.client.post(endpoint, data=payload, expect=201)
        return resp.json()
        # TODO autotmatically update components when the classes are defined
        # TODO allow ComponentType objects if you define those


    def delete_component(self, component_id):
        """ Delete component with given id """
        endpoint = "{}/components/{}".format(self.device_url, component_id)
        self.client.delete(endpoint, expect=204)
