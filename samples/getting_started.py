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

import iotkitclient

# Make sure to run python setup.py install before you begin


# Config is just used for hostname and login data
# Feel free to remove this line and replace those
# variables in the following code, or fill your
# login data in config.py
import config

# Connect to IoT Analytics host and authenticate
print("Connecting to {} ...".format(config.api_url))

# All requests to host are managed by the Client class
client = iotkitclient.Client(api_root=config.api_url, proxies=config.proxies)

# Authenticate by a username and a password. Currently, you can not create
# a user with the Python API, use the dashboard to get started
client.auth(config.username, config.password)

# IOT Analytics Cloud uses JWT authentication. For most cases, you can rely on
# the Python api to manage this, but if you need to, you can get the token
# object using the following method.
# Currently, tokens expire after one hour. You will need to recall the auth
# method upon expiration. An AuthenticationError will be raised if a Token is no
# longer valid.
token = client.get_user_token()

# Account's are organizational units. An account can be managed by multiple
# users with different roles, and a user can manage multiple accounts.
# You can create a new account simply by specifying its name.
# Please be aware that account names are not necessarily unique.
account = client.create_account("test_account")

# Tokens need to be updated to access new accounts is created. This is a
# limitation on the host side
client.auth(config.username, config.password)

# You can use the get_accounts method to retrieve a list of accounts managed by
# the current user.
accounts = client.get_accounts()

account = accounts[0]

# Device's are connected to Account's. You can create a device by specifying its
# device id and name.
new_device = account.create_device("my_device_id", "my_device_name")

# Devices need to be activated once, after activation, they are connected to
# the account performing the activation.
# Activation returns a device token, which can be used to send/retrieve data
# without a user token.
device_token = new_device.activate()

# You can get a list of all devices connected to an account using the following
# method:
devices = account.get_devices()

# If you need to access the last Response object directly, you can do so
# like this:
response = client.response
