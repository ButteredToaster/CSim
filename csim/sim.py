"""sim.py — orbital simulation state.

This is your primary workspace.  The renderer only reads:
  - sim.sun.position, sim.earth.position, sim.moon.position
  - sim.bodies  (list of Body objects for drawing)

Implement your orbital mechanics inside Simulation.step().
"""

import numpy as np


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

        # Bodies — feel free to change initial positions / radii / colors
        self.sun   = Body(
            "Sun",
            [  0,  0, 0],
            4.0,
            (255, 220,  50)
        )
        self.earth = Body(
            "Earth",
            [ 30,  0, 0],
            1.8,
            ( 70, 130, 255)
        )
        self.moon  = Body(
            "Moon",
            [ 34,  0, 0],
            0.6,
            (200, 200, 200)
        )

        # Orbital radii (display units) — edit here to change orbit sizes
        self.earth_r = np.linalg.norm(self.earth.position - self.sun.position)
        self.moon_r  = np.linalg.norm(self.moon.position  - self.earth.position)

        self.earth.tilt = np.radians(23.5)   # axial tilt, fixed

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
        earth_w = 2 * np.pi / 365.25   # rad/day — one orbit per year
        self.earth.position = np.array([
            self.earth_r * np.cos(self.t * earth_w),
            self.earth_r * np.sin(self.t * earth_w),
            0.0,
        ])

        moon_w = 2 * np.pi / 27.32     # rad/day — one orbit per lunar month
        self.moon.position = self.earth.position + np.array([
            self.moon_r * np.cos(self.t * moon_w),
            self.moon_r * np.sin(self.t * moon_w),
            0.0,
        ])

        self.earth.rotation += dt * (2 * np.pi / 1.0)   # one full rotation per day
        # ─────────────────────────────────────────────────────────────────────
