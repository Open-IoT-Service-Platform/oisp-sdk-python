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
"""User management module."""

from oisp.account import Account


# pylint: disable=too-many-instance-attributes
# The attributes match those defined in the REST API
class User:
    """Manages user information, passwords and activation."""

    # pylint: disable=too-many-arguments
    # Arguments match data provided by REST API
    def __init__(self, client, user_id, email=None, accounts=None,
                 attributes=None, tc_accepted=None, is_verified=None):
        """Create an User object.

        This method does not create a new user on host side.

        """
        self.client = client
        self.user_id = user_id
        self.email = email
        if not accounts:
            accounts = []
        self.accounts = accounts
        if not attributes:
            attributes = {}
        self.attributes = attributes
        self.tc_accepted = tc_accepted
        self.is_verified = is_verified
        self.url = "/users/{}".format(self.user_id)

    @staticmethod
    def from_json(client, json_dict):
        """Create a User object using JSON as return by REST API."""
        accounts = []
        accounts_dict = json_dict.get("accounts", {})
        for acc_id, acc_dict in accounts_dict.items():
            accounts.append(Account(client=client, name=acc_dict["name"],
                                    account_id=acc_id, role=acc_dict["role"]))
        return User(client=client, user_id=json_dict["id"],
                    email=json_dict.get("email"), accounts=accounts,
                    attributes=json_dict.get("attributes", {}),
                    tc_accepted=json_dict.get("termsAndConditions"),
                    is_verified=json_dict.get("is_verified"))

    def update_attributes(self, attributes):
        """Set user attributes dictionary.

        Entries from old attributes dictionary will not be kept if they
        are not included in the parameter.

        Args
        ----------
        attributes: Dictionary containing users new attributes.

        """
        self.client.put(self.url, data={"attributes": attributes}, expect=200)
        self.attributes = attributes

    def delete(self):
        """Delete user and connected accounts without other administrators."""
        self.client.delete(self.url)
