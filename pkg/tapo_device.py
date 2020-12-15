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

    def __init__(self, adapter, _id, p100, info):
        """
        Initialize the object.

        adapter -- the Adapter managing this device
        _id -- ID of this device
        p100 -- the P100 object to initialize from
        info -- the device info object
        """
        Device.__init__(self, adapter, _id)
        self._type = ['OnOffSwitch', 'SmartPlug']

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

    def poll(self):
        """Poll the device for changes."""
        while True:
            time.sleep(_POLL_INTERVAL)

            try:
                info = self.p100.getDeviceInfo()
                if not info:
                    self.connected_notify(False)
                    continue

                info = json.loads(info)
                if 'error_code' not in info or info['error_code'] != 0 or \
                        'result' not in info:
                    self.connected_notify(False)
                    continue

                self.connected_notify(True)
                info = info['result']

                for prop in self.properties.values():
                    prop.update(info)
            except Exception:
                self.connected_notify(False)
                continue

    def is_on(self, info):
        """
        Determine whether or not the switch is on.

        info -- current info dict for the device
        """
        return info['device_on']
