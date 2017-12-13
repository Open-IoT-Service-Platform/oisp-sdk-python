""" Module for managing user and (future) device tokens.
for IOT Analytics Cloud API"""

from datetime import datetime

import dateutil.parser

from account import Account

# pylint: disable=too-many-instance-attributes
# An attribute is required for every json field
class UserToken(object):
    """ Store user token information. """

    # pylint: disable=too-many-arguments
    # Many arguments are required as many many fields are stored
    # in this object.
    def __init__(self, value, jti, issued_by, user_id, expires_by,
                 accounts=None, typ="JWT", alg="RS256"):
        """ Create a Token

        Args:
        ----------
        value: String value of the token.
        All other arguments are contained in Repsonse from
        /auth/tokenInfo . Expires at can be given as a string
        or datetime object."""
        self.value = value
        self.typ = typ
        self.alg = alg
        self.jti = jti
        self.issued_by = issued_by
        self.user_id = user_id
        if not isinstance(expires_by, datetime):
            expires_by = dateutil.parser.parse(expires_by)
        self.expires_by = expires_by
        if not accounts:
            accounts = []
        self.accounts = accounts

    @staticmethod
    def from_json(token_str, json_dict, client):
        """ Return a Token using a JSON dictionary as obtained
        from API endpoint /auth/tokenInfo

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
        """ Return whether token is expired."""
        return datetime.now(self.expires_by.tzinfo) > self.expires_by

    def __str__(self):
        return "Token " + self.value
