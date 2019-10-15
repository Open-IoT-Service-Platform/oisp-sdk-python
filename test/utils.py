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
"""Helper methods for various tests."""
import subprocess

kubectl = ["kubectl", "-n", "oisp"]


def _run_in(cmd, deployment=None, pod=None, container=None):
    """Run command in kubernetes pod (or in random pod from deployment)."""
    assert deployment is not None or pod is not None
    if pod is None:
        out = subprocess.check_output(kubectl+["get", "pods"]).decode("utf-8")
        pods = [p for p in out.split("\n") if p.startswith(deployment+"-")]
        assert pods, "No pod in deployment {}".format(deployment)
        pod = pods[0].split()[0]
    if isinstance(cmd, str):
        cmd = cmd.split()
    if container:
        exec_ = ["exec", pod, "-c", container, "--"]
    else:
        exec_ = ["exec", pod, "--"]
    return subprocess.check_output(kubectl + exec_ + cmd,
                                   stderr=subprocess.DEVNULL)


def clear_db():
    """Reset OISP database to default.

    This clears all tables, but keeps system users.
    """
    _run_in(cmd="node /app/admin resetDB",
            deployment="dashboard", container="dashboard")


def add_user(username, password, role):
    """Add a new user.

    Args:
    ----------
    username: username for new user
    password: password for new user
    role: user role, see OISP documentation for details.
    """
    cmd = ["node", "/app/admin", "addUser", username, password, role]
    _run_in(cmd=cmd, deployment="dashboard", container="dashboard")
