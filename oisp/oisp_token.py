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
"""Module for managing user and (future) device tokens."""
from datetime import datetime

from oisp.account import Account


# pylint: disable=too-many-instance-attributes
# An attribute is required for every json field
class UserToken:
    """Store user token information."""

    # pylint: disable=too-many-arguments
    # Many arguments are required as many many fields are stored
    # in this object.
    def __init__(self, value, jti, issued_by, user_id, expires_by,
                 accounts=None, typ="JWT", alg="RS256"):
        """Create a Token.

        Args:
        ----------
        value: String value of the token.
        All other arguments are contained in Repsonse from
        /auth/tokenInfo . Expires at can be given as a string
        or datetime object.

        """
        self.value = value
        self.typ = typ
        self.alg = alg
        self.jti = jti
        self.issued_by = issued_by
        self.user_id = user_id
        if not isinstance(expires_by, datetime):
            expires_by = datetime.fromtimestamp(expires_by / 1e3)
        self.expires_by = expires_by
        if not accounts:
            accounts = []
        self.accounts = accounts

    @staticmethod
    def from_json(token_str, json_dict, client):
        """Return a Token using a JSON dictionary as obtained from REST API.

        /auth/tokenInfo.

        Args
        ----------
        token_str: Value of token as obtained from /auth/token
        js: JSON message containing access token details
        e.g.,
        Response 200 OK (application/json)
            {
                "header": {
                    "typ": "JWT",
                    "alg": "RS256"
                },
                "payload": {
                    "jti": "7b1430a2-dd61-4a47-919c-495cadb1ea7b",
                    "iss": "http://enableiot.com",
                    "sub": "53fdff4418b547e4241b8358",
                    "exp": "2014-10-02T07:53:25.361Z"
                }
            }

        """
        try:
            typ = json_dict["header"]["typ"]
            alg = json_dict["header"]["alg"]
            payload = json_dict["payload"]
            jti = payload["jti"]
            issued_by = payload["iss"]
            user_id = payload["sub"]
            expires_by = payload["exp"]
        except KeyError as exc:
            raise ValueError("Invalid JSON format key '{}' "
                             "missing".format(exc.args[0]))
        accounts = []
        for account_dict in payload.get("accounts", []):
            accounts.append(Account(client, account_dict["name"],
                                    account_dict["id"],
                                    account_dict["role"]))

        return UserToken(value=token_str, jti=jti, issued_by=issued_by,
                         user_id=user_id, expires_by=expires_by,
                         accounts=accounts, typ=typ, alg=alg)

    def is_expired(self):
        """Return whether token is expired."""
        return datetime.now(self.expires_by.tzinfo) > self.expires_by

    def __str__(self):
        return "Token " + self.value
