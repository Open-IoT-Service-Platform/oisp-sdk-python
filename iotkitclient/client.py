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
import json

import requests

from account import Account
from oic_token import UserToken
from oic_user import User


class AuthenticationError(Exception):
    """Authentication Error class for Open IOT Connector

    This Error is thrown if an error occurs before
    server is even contacted, otherwise an OIC Exception
    will be thrown, even in the case of an authentication
    related exception"""
    pass


class OICException(Exception):
    """Exception for Open IOT Connector, for cases when an
    error code is returned from the server."""

    def __init__(self, expect, resp):
        message = ("Exception during API call\n"
                   "Status code: {}, {} was expected".format(resp.status_code,
                                                             expect))
        resp_json = resp.json()
        if resp_json:
            pretty = json.dumps(resp_json, indent=4, separators=(',', ': '))
            message += "\nError message: {}".format(pretty)
        super(OICException, self).__init__(message)



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
            raise AuthenticationError("UserToken expired, you need to use "
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
        resp = self.post("/auth/token", data=payload, authorize=False,
                         expect=200)

        token_str = resp.json()["token"]
        self.user_token = self.get_user_token(token_str)
        self.user_id = self.user_token.user_id


    def get_user_token(self, token_str=None):
        """ Return a UserToken object containing user token information.

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
        resp = self.get("/auth/tokenInfo", headers=headers, authorize=False,
                        expect=200)
        return UserToken.from_json(token_str, resp.json(), client=self)


    def get_user(self, user_id=None):
        """ Get the user with given user_id. If None specified, the token
        holder will be returned."""
        if not user_id:
            user_id = self.user_token.user_id
        resp = self.get("/users/" + user_id, expect=200)
        return User.from_json(client=self, json_dict=resp.json())


    def reset_password_request_mail(self, email):
        """ Send a password reset mail to given email adress. """
        self.post("/users/forgot_password", data={"email":email},
                  authorize=False, expect=200)


    def reset_password_submit_new(self, token, password):
        """ Reset password using the token obtained via email. """
        payload = {"token":token, "password":password}
        self.put("/users/forgot_password", data=payload,
                 authorize=False, expect=200)


    def change_user_password(self, email, current_password, new_password):
        """ Change password for user identified by email. """
        url = "/users/{}/change_password".format(email)
        payload = {"currentpwd":current_password, "password":new_password}
        self.put(url, data=payload, authorize=False, expect=200)


    def request_user_activation(self, email):
        """ Send user with given email adress an activation mail."""
        self.post("/users/request_user_activation", data={"email":email},
                  authorize=False, expect=200)


    def get_server_info(self):
        """ Get cloud version and health information

        Returns: a JSON dictionary
        """
        resp = self.get("/health", authorize=False, expect=200)
        return resp.json()


    def get_accounts(self):
        """ Get a list of accounts connected to current
        authentication token. """
        return self.user_token.accounts


    def create_account(self, name):
        """ Create an account with given name and return an Account instance.

        A new token needs to be acquired using the auth method to access the
        account. """
        payload = {"name": name}
        resp = self.post("/accounts", data=payload, expect=201)
        resp_json = resp.json()
        return Account(self, resp_json["name"], resp_json["id"],
                       Account.ROLE_ADMIN)


    def _make_request(self, request_func, endpoint, authorize, expect=None,
                      *args, **kwargs):
        """ Make a request using global settings and raise an OICException
        if a status code other than expect is returned """

        headers = kwargs.pop("headers", self.get_headers(authorize=authorize))
        proxies = kwargs.pop("proxies", self.proxies)
        verify = kwargs.pop("verify", self.verify_certs)
        if "data" in kwargs and isinstance(kwargs.get("data"), dict):
            kwargs["data"] = json.dumps(kwargs["data"])
        url = self.base_url + endpoint
        resp = request_func(url, headers=headers, proxies=proxies,
                            verify=verify, *args, **kwargs)
        if expect and resp.status_code != expect:
            raise OICException(expect, resp)
        return resp

    def get(self, endpoint, authorize=True, *args, **kwargs):
        """ Make a GET request.
        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.
        """
        return self._make_request(requests.get, endpoint, authorize,
                                  *args, **kwargs)

    def post(self, endpoint, authorize=True, *args, **kwargs):
        """ Make a POST request.
        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.
        """
        return self._make_request(requests.post, endpoint, authorize,
                                  *args, **kwargs)

    def put(self, endpoint, authorize=True, *args, **kwargs):
        """ Make a PUT request.
        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.
        """
        return self._make_request(requests.put, endpoint, authorize,
                                  *args, **kwargs)

    def delete(self, endpoint, authorize=True, *args, **kwargs):
        """ Make a DELETE request.
        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.
        """
        return self._make_request(requests.delete, endpoint, authorize,
                                  *args, **kwargs)
