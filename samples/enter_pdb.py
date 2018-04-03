# Copyright (c) 2017-2018, Intel Corporation
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

"""Modify and use this file to create a debug scenario."""

import time
import os

import oisp
from oisp.utils import pretty_print

import config
import pdb

reset_db = False # True

if reset_db:
    print("Resetting DB")
    os.system("docker exec -it {} node /app/admin "
              "resetDB &> /dev/null".format(config.dashboard_container))
    os.system("docker exec -it {} node /app/admin addUser {} {} {} "
              "&> /dev/null".format(config.dashboard_container,
                                    config.username,
                                    config.password,
                                    config.role))

client = oisp.Client(api_root=config.api_url, proxies=config.proxies)
client.auth(config.username, config.password)

try:
    account = client.get_accounts()[0]
except IndexError:
    account = client.create_account("debug_account")


try:
    device = account.create_device("did", "dname", "gwid")
    device2 = account.create_device("did2", "dname2", "gwid")
    token = device.activate()
    try:
        resp = device.add_component("temp1", "temperature.v1.0")
    except oisp.OICException:
        account.create_component_type(dimension="temperature",
                                      version="1.0", ctype="sensor",
                                      data_type="Number",
                                      data_format="float",
                                      measure_unit="Degrees Celcius",
                                      display="timeSeries")
        resp = device.add_component("temp1", "temperature.v1.0")

    cid = resp["cid"]
    device_id = device.device_id
    with open("/tmp/oisp_dtoken", "w") as f:
        f.write(";".join([token, device.device_id]))

except oisp.OICException:
    with open("/tmp/oisp_dtoken", "r") as f:
        token, device_id = f.read().split(";")
    device = client.get_device(token, device_id)
    cid = device.components[0]["cid"]

device.add_sample(cid, 10)
time.sleep(.5)
device.add_sample(cid, 15)
time.sleep(.5)
device.add_sample(cid, 20, loc=(0,0))
device.submit_data()

query = oisp.DataQuery()
response = account.search_data(query)

pdb.set_trace()
