import unittest
import test.config as config

from iotkitclient import Client


class BaseCase(unittest.TestCase):

    def setUp(self):
        self.client = Client(config.api_url)
        self.client.auth(config.username, config.password)
