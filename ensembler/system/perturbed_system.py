"""
Module: System
    This module shall be used to implement subclasses of system. It wraps all information needed and generated by a simulation.
"""

import numpy as np
import pandas as pd

pd.options.mode.use_inf_as_na = True

from ensembler.util import dataStructure as data
from ensembler.util.ensemblerTypes import samplerCls, conditionCls
from ensembler.util.ensemblerTypes import Union, Iterable, NoReturn, Number

from ensembler.potentials._basicPotentials import _potential1DClsPerturbed as _perturbedPotentialCls
from ensembler.system.basic_system import system


class perturbedSystem(system):
    """
    
    """
    name = "perturbed system"
    # Lambda Dependend Settings
    state = data.lambdaState
    currentState: data.lambdaState
    potential: _perturbedPotentialCls

    # current lambda
    _currentLambda: Number = np.nan
    _currentdHdLambda: Number = np.nan

    """
    Attributes
    """

    @property
    def lam(self) -> Number:
        return self._currentLambda

    @lam.setter
    def lam(self, lam: Number):
        self._currentLambda = lam
        self.potential.set_lambda(lam=self._currentLambda)
        self._update_energies()

    def set_lambda(self, lam: float):
        self.lam = lam

    """
    Magic
    """

    def __init__(self, potential: _perturbedPotentialCls, sampler: samplerCls,
                 conditions: Iterable[conditionCls] = [],
                 temperature: float = 298.0, start_position: (Iterable[Number] or float) = None, lam: float = 0.0):
        """
            __init__
                construct a eds-System that can be used to manage a simulation.

        Parameters
        ----------
        potential:  pot.envelopedPotential, optional
            potential function class to be explored by sampling
        sampler: sampler, optional
            sampling method, that allows exploring the potential function
        conditions: Iterable[condition], optional
            conditions that shall be applied to the system.
        temperature: float, optional
            The temperature of the system (default: 298K)
        start_position:
            starting position for the simulation and setup of the system.
        lam: Number, optional
            the value of the copuling lambda
        """

        self._currentLambda = lam

        super().__init__(potential=potential, sampler=sampler, conditions=conditions, temperature=temperature,
                         start_position=start_position)
        self.set_lambda(lam)

    """
    Overwrite Functions to adapt to EDS
    """

    def set_current_state(self, current_position: Union[Number, Iterable[Number]],
                          current_velocities: Union[Number, Iterable[Number]] = 0,
                          current_force: Union[Number, Iterable[Number]] = 0,
                          current_temperature: Union[Number, Iterable[Number]] = 298,
                          current_lambda: Union[Number, Iterable[Number]] = 0,
                          current_dHdLambda: Union[Number, Iterable[Number]] = 0):
        """
            set_current_state
                set s the current state to the given variables.

        Parameters
        ----------
        Parameters
        ----------
        current_position: Union[Number, Iterable[Number]]
            new current system position
        current_velocities: Union[Number, Iterable[Number]], optional
            new current system velocity. (default: 0)
        current_force: Union[Number, Iterable[Number]], optional
            new current system force. (default: 0)
        current_temperature: Union[Number, Iterable[Number]], optional
            new current system temperature. (default: 298)
        current_lam: Union[Number, Iterable[Number]],
            The new lambda value (default: 0)
        current_dHdLam: Union[Number, Iterable[Number]],
            The new dHdLam(default: 0)
        """
        self._currentPosition = current_position
        self._currentForce = current_force
        self._currentVelocities = current_force
        self._currentTemperature = current_temperature
        self._currentLambda = current_lambda
        self._currentdHdLambda = current_dHdLambda

        self._update_energies()
        self._update_dHdLambda()
        self.update_current_state()

    def update_system_properties(self) -> NoReturn:
        """
            updateSystemProperties
                update all system properties
        """
        self._update_energies()
        self._update_temperature()
        self._update_dHdLambda()

    def update_current_state(self):
        """
        updateCurrentState
                This function updates the current state from the _current Variables.

        """
        self._currentState = self.state(position=self._currentPosition, temperature=self._currentTemperature,
                                        total_system_energy=self._currentTotE,
                                        total_potential_energy=self._currentTotPot,
                                        total_kinetic_energy=self._currentTotKin,
                                        dhdpos=self._currentForce, velocity=self._currentVelocities,
                                        lam=self._currentLambda, dhdlam=self._currentdHdLambda)

    def append_state(self, new_position: Union[Number, Iterable[Number]], new_velocity: Union[Number, Iterable[Number]], new_forces: Union[Number, Iterable[Number]],
                     new_lambda: Number) -> NoReturn:
        """
            append_state
                Append a new state to the trajectory.

        Parameters
        ----------
        new_position: Union[Number, Iterable[Number]]
            new position for the system
        new_velocity: Union[Number, Iterable[Number]]
            new velocity for the system
        new_forces: Union[Number, Iterable[Number]]
            new forces for the system
        new_lambda: Union[Number, Iterable[Number]]
            new lambda for the system

        """
        self._currentPosition = new_position
        self._currentVelocities = new_velocity
        self._currentForce = new_forces
        self._currentLambda = new_lambda

        self._update_temperature()
        self._update_energies()
        self._update_dHdLambda()
        self.update_current_state()

        self._trajectory = self._trajectory.append(self.current_state._asdict(), ignore_index=True)

    """
    Functionality
    """

    def _update_dHdLambda(self) -> Number:
        """
            _update_dHdlambda
                update the current dHdLambda value

        Returns
        -------
        Number
            dHdlambda

        """
        self._currentdHdLambda = self.potential.dvdlam(self._currentPosition)
        self.update_current_state()
        return self._currentdHdLambda
