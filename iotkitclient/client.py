# Copyright (c) 2017, Intel Corporation
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

"""@package Connect
Methods for IoT Analytics Cloud connections

"""
import dateutil.parser
import json

import requests

from token import Token
from account import Account


class AuthenticationError(Exception):
    pass


class ServerInfo(object):
    # TODO add str method
    def __init__(self, is_healthy, current_setting, name, build, date):
        # TODO documentation
        self.is_healthy = is_healthy
        self.current_setting = current_setting
        self.name = name
        self.build = build
        self.date = dateutil.parser.parse(date)

    def __str__(self):
        return ("Name {} \n"
                "Health: {} \n"
                "Setting: {}\tBuild: {}\n"
                "Date: {}".format(self.name, self.is_healthy,
                                  self.current_setting,self.build, self.date))


class Client(object):
    """ IoT Analytics Cloud client class

    Attributes:
      proxies (str): proxy server used for connection
      user_token (str): access token from IoT Analytics site connection
      user_id (str): user ID for authenticated user
    """

    def __init__(self, api_root, proxies=None, verify_certs=True):
        """ Create IoT Analytics user session, set up connection
        information (host, proxy connections) and test the connection.

        Args:
        ----------
        api_root (str): IoT Analytics server address (defaults
        to https://streammyiot.com/v1/api)
        proxies (dict, optional): dictionary of proxy server addresses
          (e.g., {"https": "http://proxy-us.mycorp.com:8080"}
        The API will respect system proxy settings if none specified.
        verify_certs (bool, optional): Whether the certificates should
        be verified on each request.
        """
        self.base_url = api_root
        self.proxies = proxies
        self.verify_certs = verify_certs
        self.user_token = None
        self.user_id = None
        # Test connection
        # TODO find documentation of health endpoint and see whether it
        # can fail in a way requests does not throw an exception
        self.get_server_info()


    def get_headers(self, authorize=True):
        """ Return a JSON dictionary containing request headers.

        Args:
        ---------
        authorized (bool, optional): Whether user token is to be included
        """
        headers = {"content-type": "application/json"}
        if not authorize:
            return headers

        if not self.user_token:
            raise AuthenticationError("You need to authenticate using "
                                      "the auth method first.")
        if self.user_token.is_expired():
            raise AuthenticationError("Token expired, you need to use "
                                      "the auth method again.")
        headers["Authorization"] = "Bearer " + self.user_token.value
        return headers


    def auth(self, username, password):
        """ Submit IoT Analytics user credentials to obtain the access token

        Sets user_id and user_token attributes for connection instance

        Args:
        ----------
        username (str): username for IoT Analytics site
        password (str): password for IoT Analytics site
        """
        payload = {"username": username, "password": password}
        resp = self._post("/auth/token", data=payload, authorize=False)

        if resp.status_code != 200:
            raise AuthenticationException("Authentication with password failed")

        token_str = resp.json()["token"]
        self.user_token = self.get_user_token(token_str)
        self.user_id = self.user_token.user_id


    def get_user_token(self, token_str=None):
        """ Return a Token object containing user token information.

        Args:
        ----------
        token_str (str): If token string is not specified, the
        last acquired token will be used.
        """
        if not token_str and self.user_token:
            return self.user_token
        if not token_str:
            raise ValueError("token_str must be specified for first token"
                             "acquisation")
        if token_str:
            headers = self.get_headers(authorize=False)
            headers["Authorization"] = "Bearer " + token_str
        else:
            headers = self.get_headers()
        # authorize=False because it is done manually, as token object NA yet
        resp = self._get("/auth/tokenInfo", headers=headers, authorize=False)

        assert resp.status_code == 200, "Could not get Token" #TODO proper errors
        return Token.from_json(token_str, resp.json(), client=self)


    def get_server_info(self): #TODO consider simply returning a json
        """ Get cloud version and health information

        Returns: a ServerInfo object
        """
        resp = self._get("/health", authorize=False)
        if resp.status_code != 200:
            raise ConnectionError("Connection failed")
        js = resp.json()
        return ServerInfo(is_healthy=js["isHealthy"], #TODO write from_json method for ServerInfo
                         current_setting=js["currentSetting"],
                         name=js["name"], build=js["build"], date=js["date"])


    def get_accounts(self): #TODO docu #TODO consider returning copy
        return self.user_token.accounts


    def create_account(self, name):
        """ Create an account with given name and return an Account instance.

        A new token needs to be acquired using the auth method to access the
        account. """
        payload = {"name": name}
        resp = self._post("/accounts", data=payload)
        assert resp.status_code == 201, "Account creation failed" #TODO proper exceptions
        js = resp.json()
        return Account(js["name"], js["id"], Account.ROLE_ADMIN, self)


    def _make_request(self, request_func, endpoint, authorize, *args, **kwargs):
        headers = kwargs.pop("headers", self.get_headers(authorize=authorize))
        proxies = kwargs.pop("proxies", self.proxies)
        verify = kwargs.pop("verify", self.verify_certs)
        if "data" in kwargs and type(kwargs.get("data")) is dict:
            kwargs["data"] = json.dumps(kwargs["data"])
        url = self.base_url + endpoint
        return request_func(url, headers=headers, proxies=proxies,
                            verify=verify, *args, **kwargs)

    def _get(self, endpoint, authorize=True, *args, **kwargs):
        return self._make_request(requests.get, endpoint, authorize,
                                  *args, **kwargs)

    def _post(self, endpoint, authorize=True, *args, **kwargs):
        return self._make_request(requests.post, endpoint, authorize,
                                  *args, **kwargs)

    def _put(self, endpoint, authorize=True, *args, **kwargs):
        return self._make_request(requests.put, endpoint, authorize,
                                  *args, **kwargs)

    def _delete(self, endpoint, authorize=True, *args, **kwargs):
        return self._make_request(requests.delete, endpoint, authorize,
                                  *args, **kwargs)
