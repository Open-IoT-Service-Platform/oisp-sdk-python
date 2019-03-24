# Copyright (c) 2015-2019, Intel Corporation
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
"""Methods for IoT Analytics Cloud connections."""

import json
import logging

import cbor
from termcolor import colored
import requests

from oisp.account import Account
from oisp.device import Device
from oisp.oisp_token import UserToken
from oisp.oisp_user import User
from oisp.utils import pretty_dumps

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)


class AuthenticationError(Exception):
    """Authentication Error class for Open IOT Connector.

    This Error is thrown if an error occurs before server is even
    contacted, otherwise an OIC Exception will be thrown, even in the
    case of an authentication related exception

    """


class OICException(Exception):
    """Exception for cases when an error code is returned from the server."""

    INVALID_REQUEST = 400
    NOT_AUTHORIZED = 401
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    ANALYTICS_ERROR = 999

    DEVICE_INVALID_DATA = 1400
    DEVICE_NOT_FOUND = 1404
    DEVICE_ALREADY_EXISTS = 1409
    INVALID_ACTIVATION_CODE = 1410
    DEVICE_SAVING_ERROR = 1500
    DEVICE_ACTIVATION_ERROR = 1510
    DEVICE_DELETION_ERROR = 1512
    DEVICE_REGISTRATION_ERROR = 1513

    USER_INVALID_DATA = 2300
    WEAK_PASSWORD = 2401
    EMAIL_NOT_VERIFIED = 2402
    ACCOUNT_LOCKED = 2403
    TERMS_AND_CONDITIONS_ERROR = 2405
    INVALID_INTERACTION_TOKEN = 2406
    USER_ALREADY_EXISTS = 2409
    USER_ALREADY_INVITED = 2420
    SOCIAL_LOGIN_NOT_CONFIGURED = 2422
    USER_SAVING_ERROR = 2500
    CANNOT_SEND_ACTIVATION_EMAIL = 2501
    USER_SAVING_ERROR_AA = 2502
    USER_DELETION_ERROR_AA = 2502
    CANNOT_REDUCE_ADMIN_PRIVILEGES = 2503

    ACCOUNT_INVALID_DATA = 3400
    CANNOT_CHANGE_TRACK_SENSOR = 3401
    ACCOUNT_NOT_FOUND = 3404
    ACCOUNT_ALREADY_EXISTS = 3409
    ACCOUNT_SAVING_ERROR = 3500
    # pylint: disable=invalid-name
    ACCOUNT_SAVING_ERROR_ADD_OR_UPDATE = 3510
    ACCOUNT_DELETION_ERROR = 3511
    ACCOUNT_DELETION_ERROR_AA = 3512

    COMPONENT_INVALID_DATA = 5400
    COMPONENT_NOT_FOUND = 5404
    COMPONENT_ALREADY_EXISTS = 5409
    SEARCH_PROCESSING_ERROR = 5410
    INVALID_PARAMETER_NAME = 5411
    INVALID_PARAMETER_VALUES = 5412

    DATA_INVALID_DATA = 6400
    FORMAT_ERROR = 6500
    # pylint: disable=invalid-name
    OFFSET_AND_LIMIT_BOTH_OR_NONE_REQUIRED = 6504
    SUBMISSION_ERROR = 6505
    WRONG_RESPONSE_CODE_FROM_AA = 6506

    RULE_INVALID_DATA = 7400
    PROPERTY_MISSING = 7401
    INVALID_SYNCHRONIZATION_STATUS = 7402
    RULE_NOT_FOUND = 7404
    RULE_ALREADY_EXISTS = 7409
    RULE_NOT_FOUND_FROM_PROXY = 7444
    RULE_DELETION_ERROR = 7557
    ACTIVATED_RULE_DELETION_ERROR = 7558
    CANNOT_USE_API = 7600

    ALERT_RULE_NOT_FOUND = 8401
    ALERT_ACCOUNT_NOT_FOUND = 8402
    ALERT_DEVICE_NOT_FOUND = 8403
    ALERT_NOT_FOUND = 8404
    WRONG_ALERT_STATUS = 8405
    ALERT_ALREADY_EXISTS = 8409
    ALERT_SAVING_ERROR_AA = 8500
    ALERT_SAVING_ERROR = 8501
    ALERT_SAVING_ERROR_COMMENTS = 8502

    INVITATION_NOT_FOUND = 10404
    INVITATION_DELETION_ERROR = 10500

    ACTUATION_SEARCH_ERROR = 12500
    ACTUATION_SAVING_ERROR = 12501

    def __init__(self, expect, resp):
        """Create OICException.

        Args
        ----------
        expect: Expected HTTP Response code
        resp: Received response object from requests.

        """
        message = ("Exception during API call\n"
                   "HTTP code: {}, {} was expected".format(resp.status_code,
                                                           expect))
        try:
            resp_json = resp.json()
            if resp_json:
                pretty = json.dumps(resp_json, indent=4,
                                    separators=(',', ': '))
                message += "\nError message: {}".format(pretty)
                self.code = resp_json.get("code")
        except json.JSONDecodeError:
            message += "\nResponse: {}".format(resp.content)
        super(OICException, self).__init__(message)


class Client:
    """IoT Analytics Cloud client class.

    Attributes:   proxies (str): proxy server used for connection
    user_token (str): access token from IoT Analytics site connection
    user_id (str): user ID for authenticated user

    """

    def __init__(self, api_root, proxies=None, verify_certs=True):
        """Set up connection.

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
        # Contains last reponse
        self.response = None
        # Test connection
        self.get_server_info()

    def get_headers(self, authorize_as=None, authorize=True):
        """Return a JSON dictionary containing request headers.

        Args:
        ---------
        authorize (bool, optional): Whether auth token is to be included
        authorize_as (optional): When using device authorization, a device
        object with a valid device_token has to be given.
        If this is None (default), client will attempt user authorization.

        """
        headers = {"Content-Type": "application/json"}
        if not authorize:
            return headers

        if authorize_as is None:
            if not self.user_token:
                raise AuthenticationError("You need to authenticate using "
                                          "the auth method first, or authorize"
                                          "as a device")
            # if self.user_token.is_expired():
            #   raise AuthenticationError("UserToken expired, you need to use "
            #                             "the auth method again.")"""
            token = self.user_token.value
        else:
            assert isinstance(authorize_as, Device), """You can only authorize
            as Device, leave authorize_as empty for user authorization."""
            token = authorize_as.device_token

        headers["Authorization"] = "Bearer " + token
        return headers

    def auth(self, username, password):
        """Submit IoT Analytics user credentials to obtain the access token.

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
        """Return a UserToken object containing user token information.

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
        """Get the user with given user_id.

        If None specified, the token holder will be returned.

        """
        if not user_id:
            user_id = self.user_token.user_id
        resp = self.get("/users/" + user_id, expect=200)
        return User.from_json(client=self, json_dict=resp.json())

    def reset_password_request_mail(self, email):
        """Send a password reset mail to given email adress."""
        self.post("/users/forgot_password", data={"email": email},
                  authorize=False, expect=200)

    def reset_password_submit_new(self, token, password):
        """Reset password using the token obtained via email."""
        payload = {"token": token, "password": password}
        self.put("/users/forgot_password", data=payload,
                 authorize=False, expect=200)

    def change_user_password(self, email, current_password, new_password):
        """Change password for user identified by email."""
        url = "/users/{}/change_password".format(email)
        payload = {"currentpwd": current_password, "password": new_password}
        self.put(url, data=payload, authorize=False, expect=200)

    def request_user_activation(self, email):
        """Send user with given email adress an activation mail."""
        self.post("/users/request_user_activation", data={"email": email},
                  authorize=False, expect=200)

    def get_server_info(self):
        """Get cloud version and health information.

        Returns: a JSON dictionary

        """
        resp = self.get("/health", authorize=False, expect=200)
        return resp.json()

    def get_accounts(self):
        """Get a list of accounts connected to current authentication token."""
        return self.user_token.accounts

    def get_device(self, device_token, device_id, domain_id=None,
                   fetch_info=True):
        """Get a device using a device token.

        Args:
        ----------
        device_token (str): as received while activating device.
        device_id (str): device id on the service.
        domain_id (str): as received while activating the device,
        this is the same as the account_id of the account the device
        is bound to.
        fetch_info (boolean): whether to fetch device information.
        """
        fetch_info = fetch_info
        headers = self.get_headers(authorize=False)
        headers["Authorization"] = "Bearer " + device_token

        url = "/devices/{}".format(device_id)
        if fetch_info:
            response = self.get(url, headers=headers, authorize=False,
                                expect=200)
            json_dict = response.json()
        else:
            json_dict = {"deviceId": device_id,
                         "domainId": domain_id}

        return Device.from_json(json_dict, client=self,
                                device_token=device_token)

    def create_account(self, name):
        """Create an account with given name and return an Account instance.

        A new token needs to be acquired using the auth method to access
        the account.

        """
        payload = {"name": name}
        resp = self.post("/accounts", data=payload, expect=201)
        resp_json = resp.json()
        return Account(self, resp_json["name"], resp_json["id"],
                       Account.ROLE_ADMIN)

    # pylint: disable=too-many-arguments
    # All arguments are necessary and this method is not exposed
    def _make_request(self, request_func, endpoint, authorize, authorize_as,
                      expect=None, *args, **kwargs):
        """Make a request using global settings.

        Raises an OICException if a status code other than expect is
        returned.

        """
        headers = kwargs.pop("headers",
                             self.get_headers(authorize=authorize,
                                              authorize_as=authorize_as))
        proxies = kwargs.pop("proxies", self.proxies)
        verify = kwargs.pop("verify", self.verify_certs)

        url = self.base_url + endpoint
        logger.debug("%s: %s", colored(request_func.__name__.upper(), "green"),
                     url)

        if "data" in kwargs and isinstance(kwargs.get("data"), dict):
            try:
                logger.debug("%s \n%s", colored("Payload (JSON):",
                                                attrs=["bold"]),
                             pretty_dumps(kwargs["data"]))
                kwargs["data"] = json.dumps(kwargs["data"])
            # Not json serializable, try CBOR
            except TypeError:
                headers["Content-Type"] = "application/cbor"
                logger.debug("%s \n%s", colored("Payload (CBOR):",
                                                attrs=["bold"]),
                             str(kwargs["data"]))
                kwargs["data"] = cbor.dumps(kwargs["data"])

        self.response = request_func(url, headers=headers, proxies=proxies,
                                     verify=verify, *args, **kwargs)

        cont_type = self.response.headers.get("Content-Type", "")
        if cont_type.startswith("application/json"):
            self.response.data = self.response.json()
        elif cont_type.startswith("application/cbor"):
            self.response.data = cbor.loads(self.response.content)

        if hasattr(self.response, "data"):
            logger.debug("%s %s \n %s \n",
                         colored("Response:", attrs=["bold"]),
                         self.response.status_code,
                         pretty_dumps(self.response.data))

        if expect and (self.response.status_code != expect):
            raise OICException(expect, self.response)
        return self.response

    def get(self, endpoint, authorize=True, authorize_as=None,
            *args, **kwargs):
        """Make a GET request.

        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.

        """
        return self._make_request(requests.get, endpoint, authorize,
                                  authorize_as, *args, **kwargs)

    def post(self, endpoint, authorize=True, authorize_as=None,
             *args, **kwargs):
        """Make a POST request.

        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.

        """
        return self._make_request(requests.post, endpoint, authorize,
                                  authorize_as, *args, **kwargs)

    def put(self, endpoint, authorize=True, authorize_as=None,
            *args, **kwargs):
        """Make a PUT request.

        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.

        """
        return self._make_request(requests.put, endpoint, authorize,
                                  authorize_as, *args, **kwargs)

    def delete(self, endpoint, authorize=True, authorize_as=None,
               *args, **kwargs):
        """Make a DELETE request.

        Args:
        ----------
        endpoint: Endpoint without the API root.
        authorize: Whether authorization token should be included.
        Other arguments are passed to requests module.

        """
        return self._make_request(requests.delete, endpoint, authorize,
                                  authorize_as, *args, **kwargs)
