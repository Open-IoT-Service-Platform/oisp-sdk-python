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

"""Helper methods for various parts.

These methods are meant to be used within the module.
"""

import json
import time
import re

from pygments import highlight, lexers, formatters


def camel_to_underscore(camel_str):
    """Convert a camelCase string to underscore_notation.

    This is useful for converting JSON style variable names
    to python style variable names.
    """
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str).lower()


def underscore_to_camel(underscore_str):
    """Convert a underscore_notation string to camelCase.

    This is useful for converting python style variable names
    to JSON style variable names.
    """
    return ''.join(w.title() if i else w
                   for i, w in enumerate(underscore_str.split('_')))


def pretty_dumps(dict_):
    """Format a json dictionary to a colorful and indented string."""
    if dict_ is None:
        return "None"
    try:
        formatted = json.dumps(dict_, indent=4)
    # Not everything is JSON serializable (see CBOR)
    except TypeError:
        formatted = str(dict_)
    return highlight(formatted,
                     lexers.find_lexer_class_by_name("JSON")(),
                     formatters.find_formatter_class("terminal")())


def pretty_print(json_dict):
    """Pretty print a JSON dictionary."""
    print(pretty_dumps(json_dict))


def timestamp_in_ms(dt=None, dtype=int):
    """Convert given datetime into UNIX timestamp.

    If dt is None, current time will be used.
    dtype is the datatype returned (int or float).
    """
    if dt is None:
        in_ms = time.time()*1e3
    else:
        in_ms = time.mktime(dt.timetuple())*1e3
    return dtype(in_ms)
