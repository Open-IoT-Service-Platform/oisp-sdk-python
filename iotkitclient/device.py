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


class Device(object):

    def __init__(self, account, device_id, name, gateway_id, domain_id,
                 created_on): #TODO include status
        self.account = account
        self.client = self.account.client
        self.device_id = device_id
        self.name = name
        self.gateway_id = gateway_id
        self.domain_id = domain_id
        self.created_on = created_on # TODO make to datetime object
        self.device_url = "/accounts/{}/devices/{}".format(account.account_id,
                                                           device_id)


    @staticmethod
    def from_json(account, js):
        return Device(account=account,
                      device_id=js.get("deviceId"), name=js.get("name"),
                      gateway_id=js.get("gatewayId"),
                      domain_id=js.get("domainId"),
                      created_on=js.get("created"))


    def delete(self):
        """ Delete device"""
        resp = self.client._delete(self.device_url, expect=204)


    def activate(self, auto_refresh_code=True,):
        """ Activate device """
        endpoint = self.device_url + "/activation"
        payload = {"activationCode": self.account.get_activation_code()} #TODO try to use cache
        resp = self.client._put(endpoint, data=payload, expect=200)


    def update(self, gateway_id=None, name=None, loc=None, tags=None,
               attributes=None): #TODO reconsider naming
        """ Change device properities """
        payload = {k:v for k,v in locals().items() if k!="self" and v}
        resp = self.client._put(self.device_url, data=payload, expect=200),
        self.__dict__.update(payload) # TODO consider updating all
