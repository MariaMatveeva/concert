"""
Each motor is associated with a :class:`Calibration` that maps arbitrary
real-world coordinates to devices coordinates. When a calibration is associated
with an motor, the position can be changed with :meth:`Motor.set_position` and
:meth:`Motor.move`::

    from concert.devices.base import LinearCalibration
    from concert.devices.motors.ankatango import ANKATangoDiscreteMotor

    calibration = LinearCalibration(1 / q.mm, 0 * q.mm)
    motor1 = ANKATangoDiscreteMotor(connection, calibration)

    motor.position = 2 * q.mm
    motor.move(-0.5 * q.mm)

As long as an motor is moving, :meth:`Motor.stop` will stop the motion.
"""
import quantities as q
import logbook
from concert.base import HardlimitError
from concert.devices.base import Device, Parameter
from concert.asynchronous import async


log = logbook.Logger(__name__)


class Motor(Device):
    """Base class for everything that moves.

    An motor is used with a *calibration* that conforms to the
    :class:`Calibration` interface to convert between user and device units.

    .. py:attribute:: position

        Motor position
    """

    STANDBY = 'standby'
    MOVING = 'moving'
    LIMIT = 'limit'

    def __init__(self, calibration, limiter=None):
        params = [Parameter('position',
                            self._get_calibrated_position,
                            self._set_calibrated_position,
                            q.m, limiter,
                            "Position of the motor")]

        super(Motor, self).__init__(params)
        self._calibration = calibration
        self._states = \
            self._states.union(set([self.STANDBY, self.MOVING, self.LIMIT]))

    @async
    def move(self, delta):
        """
        move(delta)

        Move motor by *delta* user units."""
        self.position += delta

    @async
    def stop(self):
        """
        stop()

        Stop the motion."""
        self._stop()

    @async
    def home(self):
        """
        home()

        Home motor.
        """
        self._home()

    def in_hard_limit(self):
        """Return *True* if motor device is in a limit state, otherwise
        *False*."""
        return False

    def _get_calibrated_position(self):
        return self._calibration.to_user(self._get_position())

    def _set_calibrated_position(self, position):
        self._set_state(self.MOVING)
        self._set_position(self._calibration.to_steps(position))

        if self.in_hard_limit():
            self._set_state(self.LIMIT)
            raise HardlimitError("Hard limit reached")

        self._set_state(self.STANDBY)

    def _get_position(self):
        raise NotImplementedError

    def _set_position(self, position):
        raise NotImplementedError

    def _stop(self):
        raise NotImplementedError

    def _home(self):
        raise NotImplementedError


class ContinuousMotor(Motor):
    """A movable on which one can set velocity.

    This class is inherently capable of discrete movement.

    """
    def __init__(self, position_calibration, velocity_calibration,
                 position_limiter=None, velocity_limiter=None):
        super(ContinuousMotor, self).__init__(position_calibration,
                                              position_limiter)

        param = Parameter('velocity',
                          self._get_calibrated_velocity,
                          self._set_calibrated_velocity,
                          q.m / q.s, velocity_limiter,
                          "Velocity of the motor")

        self.add_parameter(param)
        self._velocity_calibration = velocity_calibration

    def _get_calibrated_velocity(self):
        return self._velocity_calibration.to_user(self._get_velocity())

    def _set_calibrated_velocity(self, velocity):
        self._set_velocity(self._velocity_calibration.to_steps(velocity))

    def _get_velocity(self):
        raise NotImplementedError

    def _set_velocity(self, velocity):
        raise NotImplementedError


class MotorMessage(object):
    """Motor message."""
    POSITION_LIMIT = "position_limit"
    VELOCITY_LIMIT = "velocity_limit"


class Calibration(object):
    """Interface to convert between user and device units."""

    def to_user(self, value):
        """Return *value* in user units."""
        raise NotImplementedError

    def to_steps(self, value):
        """Return *value* in device units."""
        raise NotImplementedError


class LinearCalibration(Calibration):
    """A linear calibration maps a number of motor steps to a real-world unit.

    *steps_per_unit* tells how many steps correspond to some unit,
    *offset_in_steps* by how many steps the device is away from some zero
    point.
    """
    def __init__(self, steps_per_unit, offset_in_steps):
        super(LinearCalibration, self).__init__()
        self._steps_per_unit = steps_per_unit
        self._offset = offset_in_steps

    def to_user(self, value_in_steps):
        return value_in_steps / self._steps_per_unit - self._offset

    def to_steps(self, value):
        return (value + self._offset) * self._steps_per_unit
