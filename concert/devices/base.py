"""
A device is an abstraction for a piece of hardware that can be controlled.

The main interface to all devices is a generic setter and getter mechanism.
:meth:`Device.set` sets a parameter to value. Additionally, you can specify a
*blocking* parameter to halt execution until the value is actually set on the
device::

    axis.set('position', 5.5 * q.mm, blocking=True)

    # This will be set once axis.set() has finished
    camera.set('exposure-time', 12.2 * q.s)

Some devices will provide convenience accessor methods. For example, to set the
position on an axis, you can also use :meth:`.Axis.set_position`.

:meth:`Device.get` simply returns the current value.
"""
import threading
from logbook import Logger
from concert.base import Parameterizable, Parameter


log = Logger(__name__)


class Device(Parameterizable):
    """
    A :class:`Device` provides locked access to a real-world device and
    provides a :attr:`state` :class:`.Parameter`.

    A implements the context protocol to provide locking and can be used like
    this ::

        with device:
            # device is locked
            device.parameter = 1 * q.m
            ...

        # device is unlocked again

    .. py:attribute:: state

        Current state of the device.
    """

    NA = "n/a"

    def __init__(self, parameters=None):
        super(Device, self).__init__(parameters)
        self.add_parameter(Parameter('state', self._get_state,
                                     owner_only=True))
        self._lock = threading.Lock()
        self._states = set([self.NA])
        self._state = self.NA

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.release()

    def _get_state(self):
        return self._state

    def _set_state(self, state):
        if state in self._states:
            self._state = state
            self['state'].notify()
        else:
            log.warn("State {0} unknown.".format(state))
