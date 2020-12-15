"""TP-Link Tapo adapter for WebThings Gateway."""

from gateway_addon import Property


class TapoProperty(Property):
    """TP-Link Tapo property type."""

    def __init__(self, device, name, description, value):
        """
        Initialize the object.

        device -- the Device this property belongs to
        name -- name of the property
        description -- description of the property, as a dictionary
        value -- current value of this property
        """
        Property.__init__(self, device, name, description)
        self.set_cached_value(value)

    def set_value(self, value):
        """
        Set the current value of the property.

        value -- the value to set
        """
        try:
            if self.name == 'on':
                if value:
                    self.device.p100.turnOn()
                else:
                    self.device.p100.turnOff()
            else:
                return
        except Exception as e:
            print('Failed to set property:', e)
            return

        self.set_cached_value(value)
        self.device.notify_property_changed(self)

    def update(self, info):
        """
        Update the current value, if necessary.

        info -- current info dict for the device
        """
        if self.name == 'on':
            value = self.device.is_on(info)
        else:
            return

        if value != self.value:
            self.set_cached_value(value)
            self.device.notify_property_changed(self)
