from datetime import datetime

import dateutil.parser

from account import Account

class Token(object):

    def __init__(self, value, jti, issued_by, user_id, expires_by,
                 client, accounts=[], typ="JWT", alg="RS256"):
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
        if type(expires_by) is not datetime:
            expires_by = dateutil.parser.parse(expires_by)
        self.expires_by = expires_by
        self.accounts = accounts

    @staticmethod
    def from_json(token_str, js, client):
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
            typ = js["header"]["typ"]
            alg = js["header"]["alg"]
            payload = js["payload"]
            jti = payload["jti"]
            issued_by = payload["iss"]
            user_id = payload["sub"]
            expires_by = payload["exp"]
        except KeyError as e:
            raise ValueError("Invalid JSON format key '{}' "
                             "missing".format(e.args[0]))
        accounts = []
        for account_dict in payload.get("accounts", []):
            accounts.append(Account(account_dict["name"], account_dict["id"],
                                    account_dict["role"], client))

        return Token(token_str, jti, issued_by, user_id, expires_by,
                     client, accounts, typ, alg)


    def is_expired(self):
        """ Return whether token is expired."""
        return datetime.now(self.expires_by.tzinfo) > self.expires_by

    def __str__(self):
        return "Token " + self.value
