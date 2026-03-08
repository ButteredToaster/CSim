"""sim.py — orbital simulation state.

This is your primary workspace.  The renderer only reads:
  - sim.sun.position, sim.earth.position, sim.moon.position
  - sim.bodies  (list of Body objects for drawing)

Implement your orbital mechanics inside Simulation.step().
"""

import numpy as np
from csim.config import (
    SUN_RADIUS, EARTH_RADIUS, MOON_RADIUS,
    COLOR_SUN, COLOR_EARTH, COLOR_MOON,
    EARTH_ORBITAL_RADIUS, MOON_ORBITAL_RADIUS,
    EARTH_TILT_DEG, MOON_ORBITAL_TILT_DEG,
    EARTH_ORBITAL_PERIOD, MOON_ORBITAL_PERIOD, EARTH_ROTATION_PERIOD,
)


class Body:
    def __init__(self, name: str, position, radius: float, color: tuple):
        self.name     = name
        self.position = np.array(position, dtype=float)  # 3-vector, AU-ish units
        self.radius   = radius                            # display radius
        self.color    = color                             # (R, G, B) 0-255
        self.rotation = 0.0                               # current rotation angle (radians)
        self.tilt     = 0.0                               # axial tilt (radians)


class Simulation:
    def __init__(self):
        self.t = 0.0  # accumulated simulation time in days

        # Orbital radii (display units) — set in config.py
        self.earth_r = EARTH_ORBITAL_RADIUS
        self.moon_r  = MOON_ORBITAL_RADIUS

        # Bodies — colors, radii, and orbital distances are all set in config.py
        self.sun   = Body("Sun",   [0, 0, 0],                              SUN_RADIUS,   COLOR_SUN)
        self.earth = Body("Earth", [self.earth_r, 0, 0],                   EARTH_RADIUS, COLOR_EARTH)
        self.moon  = Body("Moon",  [self.earth_r + self.moon_r, 0, 0],     MOON_RADIUS,  COLOR_MOON)

        self.earth.tilt = np.radians(EARTH_TILT_DEG)

        # Renderer iterates this list; order doesn't matter (depth-sorted at draw time)
        self.bodies = [self.sun, self.earth, self.moon]

    # -------------------------------------------------------------------------
    def step(self, dt: float) -> None:
        """Advance the simulation by dt time units.

        Called once per frame.  Update self.earth.position and
        self.moon.position (and self.t) however you like.

        The sun is treated as fixed at the origin, but you can move it too.

        Placeholder below: simple circular orbits so there's something to look
        at immediately.  Replace with your own mechanics when ready.
        """
        self.t += dt

        # ── placeholder: circular orbits in the XY plane ─────────────────────
        earth_w = 2 * np.pi / EARTH_ORBITAL_PERIOD   # rad/day — one orbit per year
        self.earth.position = np.array([
            self.earth_r * np.cos(self.t * earth_w),
            self.earth_r * np.sin(self.t * earth_w),
            0.0,
        ])

        moon_w    = 2 * np.pi / MOON_ORBITAL_PERIOD     # rad/day — one orbit per lunar month
        moon_incl = np.radians(MOON_ORBITAL_TILT_DEG)
        moon_angle = self.t * moon_w
        self.moon.position = self.earth.position + np.array([
            self.moon_r * np.cos(moon_angle),
            self.moon_r * np.sin(moon_angle) * np.cos(moon_incl),
            self.moon_r * np.sin(moon_angle) * np.sin(moon_incl),
        ])

        self.earth.rotation += dt * (2 * np.pi / EARTH_ROTATION_PERIOD)   # one full rotation per day
        # ─────────────────────────────────────────────────────────────────────
