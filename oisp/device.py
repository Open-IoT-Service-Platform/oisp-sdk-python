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
"""Methods for IoT Analytics device management and data submission."""

from datetime import datetime
import uuid

from oisp.utils import (camel_to_underscore, underscore_to_camel,
                        timestamp_in_ms)


# pylint: disable=too-many-instance-attributes
# The attributes match those defined in the REST API
class Device:
    """Class managing device activation, components, and attributes.

    To find or filter devices connected to an account, refer to the
    Account class.
    """

    STATUS_CREATED = "created"
    STATUS_ACTIVE = "active"

    # pylint: disable=too-many-arguments
    # Argument match attributes as defined in the REST API
    def __init__(self, device_id, client=None, account=None, name=None,
                 status=None, gateway_id=None, domain_id=None,
                 created=None, attributes=None, components=None, tags=None,
                 loc=None, device_token=None):
        """Create a device object.

        This method does not create a device on host. For this, see
        create_device method in the Account class.
        """
        assert device_id is not None, "Device ID can not be None"
        assert account or (client and device_token and device_id), """
        Either account or both client and device_token parameters are required
        to create a device"""

        if client is None:
            client = account.client
        if not isinstance(created, datetime) and created is not None:
            created = datetime.fromtimestamp(created / 1e3)

        self.client = client
        self.account = account
        self.device_id = device_id
        self.name = name
        self.status = status
        self.gateway_id = gateway_id
        self.domain_id = domain_id
        self.created = created
        self.attributes = attributes
        self.components = components
        self.tags = tags
        self.loc = loc
        self.device_token = device_token

        self.unsent_data = []

    def __eq__(self, other):
        if not isinstance(other, Device):
            return NotImplemented
        return ((self.name, self.device_id) ==
                (other.name, other.device_id))

    @staticmethod
    def from_json(json_dict, account=None, client=None, device_token=None):
        """Create an device using json dictionary returned by the host.

        Either account or both client and device_token parameters are
        required.
        json_dict does not need to be complete, but device_id is required.

        Args:
        ----------
        json_dict: A JSON dictionary as returned by the service, does not
        need to be complete, but has to contain key "deviceId".
        account (optional): The account that the device is connected to
        client (optinal): a client object to make device related queries with.
        device_token (optional): device token as returned after activation.

        """
        device = Device(client=client,
                        account=account,
                        device_token=device_token,
                        device_id=json_dict.pop("deviceId"))
        # pylint: disable=protected-access
        device._update_with_json(json_dict)
        return device

    def _update_with_json(self, json_dict):
        """Update attributes according to json_dict.

        Args:
        ----------
        json_dict: A dictionary as returned by the service.
        """
        py_dict = {camel_to_underscore(key): value for
                   key, value in json_dict.items() if value is not None}

        created = py_dict.get("created")
        if not isinstance(created, datetime) and created is not None:
            py_dict["created"] = datetime.fromtimestamp(created / 1e3)
        if "loc" in py_dict:
            py_dict["loc"] = list(map(int, py_dict["loc"]))
        self.__dict__.update(py_dict)

    @property
    def url(self):
        """Return base url for device."""
        if self.account is not None:
            return "/accounts/{}/devices/{}".format(self.account.account_id,
                                                    self.device_id)
        return "/devices/{}".format(self.device_id)

    @property
    def auth_as(self):
        """Return default authorization strategy.

        If device has a device token, it will authorize at itself,
        otherwise, it will try to use the user token in its registered
        client (default behaviour in Client, hence None returned).
        """
        return self if self.device_token else None

    def delete(self):
        """Delete device.

        This needs a client with login, device authorization
        is not sufficent for delete operation.
        """
        self.client.delete(self.url, expect=204)

    def activate(self, activation_code=None):
        """Activate device, return dictionary containing device token.

        Args
        ----------
        activation_code (optional): Activation code got from account,
        if no activation code is given but an account object is
        present (for example if device object is created using the
        Account.create_device method), one will automatically be requested.
        """
        if activation_code is None:
            assert self.account is not None, """Activation code is needed
            for devices without an account."""
            activation_code = self.account.get_activation_code()

        endpoint = self.url + "/activation"
        payload = {"activationCode": activation_code}
        response = self.client.put(endpoint, data=payload, expect=200)
        account_id = response.json().get("domainId")

        if self.account is not None:
            assert self.account.account_id == account_id, """Account ID does
            not match activation code"""
        self.domain_id = account_id
        self.device_token = response.json().get("deviceToken")
        return self.device_token

    # pylint: disable=unused-argument
    # The arguments are accesses through locals()
    def set_properties(self, gateway_id=None, name=None, loc=None, tags=None,
                       attributes=None):
        """Change device properities."""
        payload = {underscore_to_camel(k): v
                   for k, v in locals().items() if k != "self" and v}

        self.client.put(self.url, data=payload, expect=200,
                        authorize_as=self.auth_as)
        self.__dict__.update(payload)

    def add_component(self, name, component_type, cid=None):
        """Add a new component to the device.

        Returns a dictionary containing name, type, deviceId and cid,
        but the component_types list is not updated to save a request.

        Args
        ----------
        name: Component name
        component_type: Component type as listed in Component Catalog
        cid: Unique component id. If None specified, a UUID will be
        generated.

        """
        endpoint = self.url + "/components"
        if not cid:
            cid = str(uuid.uuid4())
        payload = {"cid": cid, "name": name, "type": component_type}
        resp = self.client.post(endpoint, data=payload,
                                authorize_as=self.auth_as, expect=201)

        if self.components is None:
            self.components = []

        self.components.append(resp.json())
        return resp.json()

    def delete_component(self, component_id):
        """Delete component with given id."""
        endpoint = "{}/components/{}".format(self.url, component_id)
        self.client.delete(endpoint, authorize_as=self.auth_as, expect=204)
        self.components = [c for c in self.components
                           if c["cid"] != component_id]

    def update(self):
        """Update device information."""
        resp = self.client.get(self.url, authorize_as=self.auth_as, expect=200)
        self._update_with_json(resp.json())

    def add_sample(self, component_id, value, on=None, loc=None):
        """Add a single datapoint.

        Use the submit_data method to send data to the
        OISP cloud.

        Args:
        ----------
        component_id: Id of the component datapoint belongs to.
        value: Value of datapoint.
        on (optional): Timestamp in milliseconds, if this is omitted,
        current time will be used instead.
        location (optional): Location of the device as the data
        was recorded.
        """
        if on is None:
            on = timestamp_in_ms()
        datapoint = {"componentId": component_id,
                     "value": value,
                     "on": on}
        if loc is not None:
            datapoint["loc"] = loc
        self.unsent_data.append(datapoint)

    def submit_data(self, on=None):
        """Submit data.

        Data needs to be added using the add_datapoint method before.

        Args:
        ----------
        on (optional): Timestamp in milliseconds, if this is omitted,
        current time will be used instead.
        """
        payload = {"on": timestamp_in_ms(on),
                   "accountId": self.domain_id,
                   "data": self.unsent_data}

        # If there is an account, we can POST to device URL
        if self.auth_as is None:
            url = self.url
            raise Warning("""Submitting data without account token is """
                          """currently not supported.""")
        # Otherwise we need to use the alternative /data/.* URL
        else:
            url = "/data/{}".format(self.device_id)

        self.client.post(url, data=payload, authorize_as=self.auth_as,
                         expect=201)

        self.unsent_data = []
