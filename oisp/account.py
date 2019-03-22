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
"""Methods for IoT Analytics account management."""

from oisp.data_query import DataQuery, QueryResponse
from oisp.device import Device


# pylint: disable=too-many-instance-attributes
# The attributes match those defined in the REST API
class Account:
    """Create IoT Account instance."""

    ROLE_ADMIN = "admin"
    ROLE_USER = "user"

    def __init__(self, client, name, account_id, role):
        """Create account object."""
        self.client = client
        self.name = name
        self.account_id = account_id
        self.role = role
        self.activation_code = None
        self.url = "/accounts/{}".format(self.account_id)

    def __str__(self):
        return "Account | name: {}\tid:{}\trole:{}".format(self.name,
                                                           self.account_id,
                                                           self.role)

    def __eq__(self, other):
        if not isinstance(other, Account):
            return NotImplemented
        return ((self.name, self.account_id, self.role) ==
                (other.name, other.account_id, other.role))

    def delete(self):
        """Delete account."""
        self.client.delete(self.url, expect=204)
        self.client.user_token.accounts.pop(self)

    def get_activation_code(self, auto_refresh=True):
        """Return previous activation code a string if it is still valid.

        If auto_refresh is True (default), this will automatically
        request a new activation code if the old one is expired.
        Otherwise it will return None

        """
        endpoint = self.url + "/activationcode"
        resp = self.client.get(endpoint, expect=200)
        activation_code = resp.json()["activationCode"]
        # time_left = resp.json()["timeLeft"]
        if not activation_code and auto_refresh:
            activation_code = self.refresh_activation_code()
        self.activation_code = activation_code
        return activation_code

    def refresh_activation_code(self):
        """Request a new activation code from server.

        Returns the activation code as string.

        """
        endpoint = self.url + "/activationcode/refresh"
        resp = self.client.put(endpoint, expect=200)
        self.activation_code = resp.json()["activationCode"]
        return self.activation_code

    # pylint: disable=unused-argument, too-many-arguments
    # Arguments are accessed via locals() and as many as API parameters are
    # necessary
    def get_devices(self, sort=None, order=None, limit=None, skip=None,
                    device_id=None, gateway_id=None, name=None, status=None):
        """Get a list of devices connected to the account.

        Args
        ----------
        sort (str): sort result by this attributes (example: device_id, name)
        order (str): "asc" for ascending, "desc" for descending order.
        limit (int): Limit number of results to this number
        skip (int): Skip this many elements at the beginning.
        device_id (str): Filter by device id
        gateway_id (str): Filter by gateway id
        name (str): Filter by name
        status (str): Filter by status

        """
        endpoint = self.url + "/devices"
        endpoint += "&".join(["{}={}".format(param, locals().get(param))
                              for param in ["sort", "order", "limit", "skip",
                                            "device_id", "gateway_id", "name",
                                            "status"]
                              if locals().get(param) is not None])

        resp = self.client.get(endpoint, expect=200)
        devices = []
        for device_json in resp.json():
            devices.append(Device.from_json(device_json, account=self))
        return devices

    def get_device(self, device_id):
        """Get device with given id."""
        endpoint = self.url + "/devices/" + device_id
        resp = self.client.get(endpoint, 200)
        return Device.from_json(resp.json(), account=self)

    def create_device(self, device_id, name, gateway_id=None, tags=None,
                      loc=None, attributes=None):
        """Create a device.

        Device ID has to be unique.

        """
        endpoint = "/accounts/{}/devices".format(self.account_id)
        if gateway_id is None:
            gateway_id = device_id
        payload = {"deviceId": device_id,
                   "gatewayId": gateway_id, "name": name}
        if tags:
            payload["tags"] = tags
        if loc:
            payload["loc"] = loc
        if attributes:
            payload["attributes"] = attributes
        resp = self.client.post(endpoint, data=payload, expect=201)
        return Device.from_json(resp.json(), account=self)

    def get_device_tags(self):
        """Return a list of all device tags."""
        endpoint = self.url + "/devices/tags"
        resp = self.client.get(endpoint, expect=200)
        return resp.json()

    def get_device_attributes(self):
        """Return a dictionary of all device attributes.

        Each entry contains a list for all values for an attribute

        """
        endpoint = self.url + "/devices/attributes"
        resp = self.client.get(endpoint, expect=200)
        return resp.json()

    def get_component_types_catalog(self, full=False):
        """Return a JSON list, containing dictionaries for component types."""
        endpoint = self.url + "/cmpcatalog"
        if full:
            endpoint += "?full=true"
        resp = self.client.get(endpoint, expect=200)
        return resp.json()

    def create_component_type(self, dimension, version, ctype, data_type,
                              data_format, measure_unit, display,
                              min_val=None, max_val=None, command=None):
        """Create a component type.

        Args:
        ----------
        See API documentation for endpoint /{account_id}/cmpcatalog, below
        are some examples for each parameter:
        dimension (str): "temperature"
        version (str): "1.0", "2.0"
        ctype: "sensor" | "actuator"
        data_type: "Number" | "String" | "Boolean" | "ByteArray"
        data_format: "float" | "boolean" | "string" | "percentage" | "integer"
        measure_unit (str): "Degress Celcius"
        display: "timeSeries", "rawData", "binaryDataRenderer"
        min_val (optional): minimum value
        max_val (optional): maximum value
        """
        endpoint = self.url + "/cmpcatalog"
        payload = {"dimension": dimension, "version": version, "type": ctype,
                   "dataType": data_type, "format": data_format,
                   "measureunit": measure_unit, "display": display}

        if min_val:
            payload["min"] = min_val
        if max_val:
            payload["max"] = max_val
        if command:
            payload["command"] = command
        self.client.post(endpoint, data=payload, expect=201)

    def update_component_type(self, component_type_id, dimension=None,
                              ctype=None, data_type=None, data_format=None,
                              measure_unit=None, display=None,
                              min_val=None, max_val=None):
        """Update a component type.

        Minor version info will be incremented by 1, returns updated component
        type as dictionary

        Args:
        ----------
        See Account.create_component_type
        """
        endpoint = self.url + "/cmpcatalog/{}".format(component_type_id)
        payload = {}
        if dimension:
            payload["dimension"] = dimension
        if ctype:
            payload["type"] = ctype
        if data_type:
            payload["dataType"] = data_type
        if data_format:
            payload["format"] = data_format
        if measure_unit:
            payload["measureunit"] = measure_unit
        if display:
            payload["display"] = display
        if min_val:
            payload["min"] = min_val
        if max_val:
            payload["max"] = max_val
        resp = self.client.put(endpoint, data=payload, expect=201)
        return resp.json()

    def get_component_type(self, component_type_id):
        """Return a JSON dictionary containing component type information."""
        endpoint = self.url + "/cmpcatalog/{}".format(component_type_id)
        resp = self.client.get(endpoint, expect=200)
        return resp.json()

    def search_data(self, query):
        """Search for data accessible to the account.

        Args:
        ----------
        query: An oisp.DataQuery object or a json dictionary.
        """
        if isinstance(query, DataQuery):
            payload = query.json()
        else:
            payload = query
        endpoint = self.url + "/data/search/advanced"
        data_dict = self.client.post(endpoint, data=payload, expect=200).data
        return QueryResponse(self, data_dict)
