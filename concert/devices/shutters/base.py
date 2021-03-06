from concert.devices.base import Device
from concert.asynchronous import async


class Shutter(Device):
    OPEN = "open"
    CLOSED = "closed"

    """Shutter device."""
    def __init__(self):
        super(Shutter, self).__init__()
        self._states = self._states.union(set([self.OPEN, self.CLOSED]))
        self._state = self.NA

    @async
    def open(self):
        """open()

        Open the shutter."""
        self._open()

    @async
    def close(self):
        """close()

        Close the shutter."""
        self._close()

    def _open(self):
        raise NotImplementedError

    def _close(self):
        raise NotImplementedError
