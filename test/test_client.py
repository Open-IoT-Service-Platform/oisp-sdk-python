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

import unittest
import test.config as config
from test.basecase import BaseCase

import oisp


class AuthTestCase(BaseCase):

    def test_connection(self):
        client = oisp.Client(config.api_url, proxies=config.proxies)

    def test_auth_fail(self):
        wrong_password = "wrong_password"
        client = oisp.Client(config.api_url, proxies=config.proxies)

        login_sucessful_with_wrong_password = True
        try:
            client.auth(config.username, wrong_password)
        except oisp.client.OICException as e:
            self.assertEqual(e.code,
                             oisp.client.OICException.NOT_AUTHORIZED)
            login_sucessful_with_wrong_password = False

        self.assertFalse(login_sucessful_with_wrong_password)

    def test_auth_success(self):
        client = oisp.Client(config.api_url, proxies=config.proxies)
        client.auth(config.username, config.password)


class GetCreateAccountTestCase(BaseCase):

    def test_get_create_account(self):
        accounts = self.client.get_accounts()
        self.assertEqual(accounts, [])
        account = self.client.create_account("test_account")
        # Reauth to access new Account
        self.client.auth(config.username, config.password)
        accounts = self.client.get_accounts()
        self.assertEqual(accounts, [account])
