import unittest
import test.config as config

from iotkitclient import Client


class BaseCase(unittest.TestCase):
    """ Test case that creates a connection to server as
        configured in config.py in test directory. """

    def setUp(self):
        self.client = Client(config.api_url)
        self.client.auth(config.username, config.password)
