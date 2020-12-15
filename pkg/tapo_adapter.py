"""TP-Link Tapo adapter for WebThings Gateway."""

from gateway_addon import Adapter, Database
from PyP100 import PyP100
import json

from .tapo_device import TapoDevice


_TIMEOUT = 3


class TapoAdapter(Adapter):
    """Adapter for TP-Link Tapo smart home devices."""

    def __init__(self, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        self.name = self.__class__.__name__
        Adapter.__init__(self,
                         'tapo-adapter',
                         'tapo-adapter',
                         verbose=verbose)

        self.username = None
        self.password = None
        self.addresses = []

        database = Database(self.package_name)
        if database.open():
            config = database.load_config()

            if 'username' in config and len(config['username']) > 0:
                self.username = config['username']

            if 'password' in config and len(config['password']) > 0:
                self.password = config['password']

            if 'addresses' in config:
                self.addresses = config['addresses']

            database.close()

        self.pairing = False
        self.start_pairing(_TIMEOUT)

    def _add_from_config(self):
        """Attempt to add all configured devices."""
        for address in self.addresses:
            try:
                p100 = PyP100.P100(address, self.username, self.password)
                p100.handshake()
                p100.login()
            except Exception as e:
                print('Failed to connect to {}: {}'.format(address, e))
                continue

            self._add_device(address, p100)

    def start_pairing(self, timeout):
        """
        Start the pairing process.

        timeout -- Timeout in seconds at which to quit pairing
        """
        if self.username is None or self.password is None or self.pairing:
            return

        self.pairing = True

        self._add_from_config()

        # TODO: add discovery when it's available

        self.pairing = False

    def _add_device(self, address, p100):
        """
        Add the given device, if necessary.

        address -- IP address of the device
        p100 -- the P100 object
        """
        info = p100.getDeviceInfo()
        if not info:
            print('Failed to retrieve device info')
            return

        try:
            info = json.loads(info)
        except ValueError:
            print('Failed to decode device info: {}'.format(info))
            return

        if 'error_code' not in info or info['error_code'] != 0:
            print('Received error code: {}'.format(info['error_code']))
            return

        if 'result' not in info:
            print('Invalid device info: {}'.format(info))
            return

        info = info['result']

        _id = 'tapo-' + info['device_id']
        if _id not in self.devices:
            device = TapoDevice(self, _id, address, p100, info)
            self.handle_device_added(device)

    def cancel_pairing(self):
        """Cancel the pairing process."""
        self.pairing = False
