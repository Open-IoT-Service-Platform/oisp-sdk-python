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
import docker

# IoT Analytics server info#
api_url = "http://localhost/v1/api"
proxies = None

# container names (leave None to try to autodetect)
dashboard_cont = None
postgres_cont = None

# user account to use
username = "oisp@testing.com"
password = "OispTesting1"
role = "admin"

# account data
accountname = "testaccount"


def _get_container_names_containing(string):
    dc = docker.DockerClient()
    return [c.name for c in dc.containers.list() if string in c.name]


if dashboard_cont is None:
    cont_names = _get_container_names_containing("frontend")
    assert len(cont_names) == 1, "Could not autodetect container \
    name (too many/few candidates)"
    dashboard_cont = cont_names[0]

if postgres_cont is None:
    cont_names = _get_container_names_containing("postgres")
    assert len(cont_names) == 1, "Could not autodetect container \
    name (too many candidates)"
    postgres_cont = cont_names[0]
