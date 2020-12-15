"""TP-Link Tapo adapter for WebThings Gateway."""

from gateway_addon import Device
import base64
import json
import threading
import time

from .tapo_property import TapoProperty


_POLL_INTERVAL = 5


class TapoDevice(Device):
    """TP-Link Tapo device type."""

    def __init__(self, adapter, _id, address, p100, info):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        address -- IP address
        p100 -- the P100 object to initialize from
        info -- the device info object
        """
        Device.__init__(self, adapter, _id)
        self._type = ['OnOffSwitch', 'SmartPlug']

        self.address = address
        self.p100 = p100
        self.description = info['model']

        if 'nickname' in info and len(info['nickname']) > 0:
            self.name = base64.b64decode(info['nickname']).decode('utf8')
        else:
            self.name = self.description

        self.properties['on'] = TapoProperty(
            self,
            'on',
            {
                '@type': 'OnOffProperty',
                'title': 'On/Off',
                'type': 'boolean',
            },
            self.is_on(info)
        )

        t = threading.Thread(target=self.poll)
        t.daemon = True
        t.start()

    def reconnect(self):
        """Reconnect the P100 object."""
        self.p100.handshake()
        self.p100.login()

    def poll(self):
        """Poll the device for changes."""
        while True:
            time.sleep(_POLL_INTERVAL)

            try:
                info = self.p100.getDeviceInfo()
                if not info:
                    raise Exception('Failed to retrieve device info')

                info = json.loads(info)

                if 'error_code' not in info or info['error_code'] != 0:
                    raise Exception(
                        'Received error code: {}'.format(info['error_code'])
                    )

                if 'result' not in info:
                    raise Exception('Invalid device info: {}'.format(info))

                self.connected_notify(True)
                info = info['result']

                for prop in self.properties.values():
                    prop.update(info)
            except Exception as e:
                print('Failed to poll device: {}'.format(e))
                self.connected_notify(False)

                # Try to reconnect
                try:
                    self.reconnect()
                except Exception:
                    pass

                continue

    def is_on(self, info):
        """
        Determine whether or not the switch is on.

        info -- current info dict for the device
        """
        return info['device_on']
