# Copyright (c) 2017-2018, Intel Corporation
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

"""Tools for building search queries."""

import datetime

from oisp.device import Device
from oisp.utils import underscore_to_camel, timestamp_in_ms


# pylint: disable=too-few-public-methods
# Further methods are going to be added for non REST API
# and this class is meant to act as a base class for further queries,
# so it can not be replaced with a method.
class DataQuery:
    """Class to build JSON queries in an object oriented manner."""

    AGGREGATION_INCLUDE = "include"
    AGGREGATION_EXCLUDE = "exclude"
    AGGREGATION_ONLY = "only"

    SORTBY_TIMESTAMP = "Timestamp"
    SORTBY_VALUE = "Value"
    SORT_ASC = "Asc"
    SORT_DESC = "Desc"

    __VALID_PARAMS = ["from_", "to", "gateway_ids", "device_ids",
                      "component_ids", "returned_measure_attributes",
                      "show_measure_location", "aggregations",
                      "dev_comp_attribute_filter",
                      "measurement_attribute_filter", "value_filter",
                      "component_first_row", "component_row_limit",
                      "sort", "additional_properties"]

    # pylint: disable=unused-argument, too-many-arguments, too-many-locals
    def __init__(self, from_=0, to=None, gateway_ids=None, device_ids=None,
                 component_ids=None, returned_measure_attributes=None,
                 show_measure_location=None, aggregations=None,
                 dev_comp_attribute_filter=None,
                 measurement_attribute_filter=None, value_filter=None,
                 component_first_row=None, component_row_limit=None,
                 sort=None, additional_properties=None):
        """Create a data query object.

        All parameters match those in the service API,
        from is renamed to from_ to avoid the python keyword.
        from_ and to can be datetime objects, device_ids is a list
        containing ids, or Device objects or a mixture of both.
        """
        for k, v in locals().items():
            if k in DataQuery.__VALID_PARAMS:
                setattr(self, k, v)

    # pylint: disable=no-member
    # pylint does not recognize dynamically created members
    def json(self):
        """Return a JSON dictionary representing the query."""
        payload_dict = {underscore_to_camel(k): v
                        for k, v in self.__dict__.items()
                        if k in DataQuery.__VALID_PARAMS and v is not None}

        if isinstance(self.from_, datetime.datetime):
            payload_dict["from"] = timestamp_in_ms(self.from_)

        if isinstance(self.to, datetime.datetime):
            payload_dict["to"] = timestamp_in_ms(self.to)
        # instead of device_ids device objects can be used
        for i, dev in enumerate(payload_dict.get("device_ids", [])):
            if isinstance(dev, Device):
                payload_dict["device_ids"][i] = dev.device_id

        return payload_dict


class QueryResponse:
    """Class to manage data search responses."""

    ADVANCED_INQUIRY = "advancedDataInquiryResponse"
    DATATYPE_NUMBER = "number"

    def __init__(self, account, json_dict, query=None):
        """Create QueryResponse object.

        Args:
        ----------
        account: Account which made the inquiry.
        json_dict: Response from the service.
        query (DataQuery; optional): Query for the response.
        """
        self.account = account
        self.json_dict = json_dict
        self.query = query

        assert json_dict.get("msgType") == QueryResponse.ADVANCED_INQUIRY, """
        Only advanced inquiry responses are supported."""
        assert account.account_id == json_dict.get("accountId"), """
        Account ID mismatch."""

        # datetime uses timestamps in seconds, the service in ms
        start_ts = json_dict.get("startTimestamp") / 1e3
        end_ts = json_dict.get("endTimestamp") / 1e3
        self.start_time = datetime.datetime.fromtimestamp(start_ts)
        self.end_time = datetime.datetime.fromtimestamp(end_ts)

        self._parse_samples()

    def _parse_samples(self):
        self.samples = []
        data = self.json_dict.get("data", [])
        for device_dict in data:
            device_id = device_dict["deviceId"]
            for component_dict in device_dict.get("components"):
                component_id = component_dict["componentId"]
                date_type = component_dict["dataType"]
                ts_i = component_dict["samplesHeader"].index("Timestamp")
                val_i = component_dict["samplesHeader"].index("Value")
                for sample_list in component_dict.get("samples", []):
                    timestamp = sample_list[ts_i]
                    value = sample_list[val_i]
                    if date_type == QueryResponse.DATATYPE_NUMBER:
                        value = float(value)
                    # datetime uses timestamps in seconds, the service in ms
                    timestamp = float(timestamp)/1e3
                    on = datetime.datetime.fromtimestamp(timestamp)
                    sample = Sample(self, device_id, component_id, value, on)
                    self.samples.append(sample)


class Sample:
    """Class representing a single datapoint."""

    # pylint: disable=too-many-arguments
    def __init__(self, response, device_id, component_id, value, on, loc=None):
        """Create Sample object.

        Args:
        ----------
        response: QueryResponse object the sample belongs to.
        device_id: As returned by the service.
        component_id: As returned by the service.
        value: Sample value, converted to correct type
        on: timestamp (in microseconds) or datetime object
        loc (optional): location as iterable with 2 or 3 elements.
        """
        self.response = response
        self.device_id = device_id
        self.component_id = component_id
        self.value = value
        if not isinstance(on, datetime.datetime):
            on = datetime.datetime.fromtimestamp(float(on)/10e6)
        self.on = on
        self.loc = loc
        self._device = None

    @property
    def device(self):
        """Device object got using device_id.

        If the property is read for the first time, this will make an
        API call.
        """
        if self._device is None:
            self._device = self.response.account.get_device(self.device_id)
        return self._device

    def __str__(self):
        return "{}:{}".format(self.on, self.value)
