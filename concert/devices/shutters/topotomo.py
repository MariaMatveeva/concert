'''
Created on Apr 12, 2013

@author: farago
'''
from concert.devices.shutters import base
from concert.connections.tango import TopoTomo


class Shutter(base.Shutter):
    def __init__(self, index):
        if index < 0 or index > 2:
            raise ValueError("Index must be in range [0-2].")

        super(Shutter, self).__init__()
        self._device = TopoTomo().get_device("iss/toto/rato_toto")
        self._index = index
        self._opened = None
        self.close().wait()

    @property
    def index(self):
        return self._index

    def is_open(self):
        return self._opened

    def _open(self):
        self._device.DoSPECTextCommand("shopen %d" % (self.index))
        self._opened = True

    def _close(self):
        self._device.DoSPECTextCommand("shclose %d" % (self.index))
        self._opened = False
