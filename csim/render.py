"""render.py — 3D perspective renderer for the solar system simulation.

How it works
------------
Camera
  An orbit camera defined by spherical coordinates (theta = elevation,
  phi = azimuth) around a target point.  Controls are handled in
  Renderer.handle_input() and mapped to WASD / arrow keys + zoom.

Projection
  Standard pinhole perspective.  A world-space point P is transformed
  into camera space via the (right, up, fwd) basis, then divided by
  depth and scaled by the focal length to get screen coordinates.

Sphere shading
  For each body the projected screen radius is computed.  Every pixel
  inside that circle gets a surface normal derived from its screen-space
  offset from the projected centre (nx = dx/sr, ny = dy/sr, nz = sqrt(…)).
  A diffuse term is computed as dot(N, L) in camera space, combined with
  a small ambient term, and multiplied into the body's base colour.
  The sun is treated as an emissive (unshaded) light source with a glow.

Trails
  The last TRAIL_LEN positions of each non-sun body are stored and drawn
  as fading dots behind the body.

A faint reference grid of concentric circles in the z=0 plane gives a
sense of depth and scale.
"""

from __future__ import annotations
from collections import deque
from datetime import datetime
import numpy as np
import pygame
from PIL import Image
from csim.config import (
    CAMERA_FOV_DEG, CAMERA_DISTANCE, CAMERA_THETA_DEG, CAMERA_PHI_DEG,
    COLOR_AXIS, COLOR_LONGITUDE, COLOR_GRID,
    COLOR_HUD, COLOR_SPEED, COLOR_COORDS, COLOR_MOON_PHASE,
    TRAIL_LEN, TRAIL_FADE,
    SIM_SPEED_DEFAULT_HOURS,
    AMBIENT, DIFFUSE, TERMINATOR_WIDTH, DIFFUSE_GAMMA,
    SUN_GLOW_LAYERS,
    LONGITUDE_COUNT, LONGITUDE_HALF_WIDTH,
    GRID_RADII,
)


class Camera:
    def __init__(self, width: int, height: int, fov_deg: float = CAMERA_FOV_DEG):
        self.width    = width
        self.height   = height
        self.focal    = (width / 2.0) / np.tan(np.radians(fov_deg / 2.0))
        self.theta    = np.radians(CAMERA_THETA_DEG)   # elevation
        self.phi      = np.radians(CAMERA_PHI_DEG)     # azimuth
        self.distance = CAMERA_DISTANCE
        self.target   = np.zeros(3)

    @property
    def position(self) -> np.ndarray:
        ct, st = np.cos(self.theta), np.sin(self.theta)
        cp, sp = np.cos(self.phi),   np.sin(self.phi)
        return self.target + self.distance * np.array([ct*cp, ct*sp, st])

    def basis(self):
        fwd = self.target - self.position
        fwd /= np.linalg.norm(fwd)
        hint = np.array([0., 0., 1.])
        if abs(np.dot(fwd, hint)) > 0.99:
            hint = np.array([0., 1., 0.])
        right = np.cross(fwd, hint);  right /= np.linalg.norm(right)
        up    = np.cross(right, fwd)
        return right, up, fwd

    def project(self, p: np.ndarray):
        right, up, fwd = self.basis()
        d     = p - self.position
        depth = np.dot(d, fwd)
        if depth <= 0.1:
            return None
        sx = self.width  / 2.0 + np.dot(d, right) / depth * self.focal
        sy = self.height / 2.0 - np.dot(d, up)    / depth * self.focal
        return sx, sy, depth

    def project_radius(self, p: np.ndarray, r: float):
        res = self.project(p)
        if res is None:
            return None, None, None
        sx, sy, depth = res
        return sx, sy, r / depth * self.focal


class Renderer:
    TRAIL_LEN    = TRAIL_LEN
    _PHASE_NAMES = [
        "New Moon",       "Waxing Crescent", "First Quarter",  "Waxing Gibbous",
        "Full Moon",      "Waning Gibbous",  "Third Quarter",  "Waning Crescent",
    ]

    def __init__(self, screen: pygame.Surface, trail_interval: float = 1.0):
        """
        trail_interval: minimum sim-time (days) between recorded trail dots.
            1/24  → once per hour
            0.5   → once per 12 hours
            1.0   → once per day  (default)
        """
        self.screen         = screen
        w, h                = screen.get_size()
        self.camera         = Camera(w, h)
        self.trail_interval = trail_interval
        self._trails:       dict[str, deque] = {}
        self._last_record:  dict[str, float] = {}   # body name → last recorded sim.t
        self._font          = pygame.font.SysFont("monospace", 13)
        self._sim_speed_hours = SIM_SPEED_DEFAULT_HOURS   # internal unit: hours; 24 = 1 day/s
        self._speed_timer     = 0.0
        self._coord_mode    = 0    # 0 = cartesian, 1 = cylindrical, 2 = spherical
        self._recording     = False
        self._frames: list  = []

    # ── public ────────────────────────────────────────────────────────────────

    def record_toggle(self) -> None:
        if not self._recording:
            self._recording = True
            self._frames = []
        else:
            self._recording = False
            if self._frames:
                fname = datetime.now().strftime("recording_%Y%m%d_%H%M%S.gif")
                first = self._frames[0]
                first.save(fname, save_all=True, append_images=self._frames[1:],
                           loop=0, duration=33)
                print(f"GIF saved: {fname}")
            self._frames = []

    @property
    def sim_speed(self) -> float:
        return self._sim_speed_hours / 24.0

    def cycle_coord_mode(self) -> None:
        self._coord_mode = (self._coord_mode + 1) % 3

    def handle_input(self, keys, dt: float) -> None:
        rot  = 1.4 * dt
        zoom = 45.0 * dt
        lim  = np.radians(89.0)
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.camera.phi   += rot
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.camera.phi   -= rot
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.camera.theta  = min( lim, self.camera.theta + rot)
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.camera.theta  = max(-lim, self.camera.theta - rot)
        if keys[pygame.K_EQUALS]                   : self.camera.distance = max(10.0, self.camera.distance - zoom)
        if keys[pygame.K_MINUS]                    : self.camera.distance += zoom

        # Speed adjustment on hold — fire once per 0.07s (~14 steps/sec)
        self._speed_timer += dt
        if self._speed_timer >= 0.07:
            self._speed_timer = 0.0
            step = 24 if self._sim_speed_hours >= 48 else 1
            if keys[pygame.K_COMMA] and self._sim_speed_hours > 1:
                self._sim_speed_hours = max(1, self._sim_speed_hours - step)
            if keys[pygame.K_PERIOD]:
                self._sim_speed_hours += step

    def render(self, sim, paused: bool) -> None:
        self._record_trails(sim)
        self._draw_grid()
        self._draw_trails()
        self._draw_bodies(sim)
        self._draw_hud(sim, paused)
        self._draw_coords(sim)
        self._draw_moon_phase(sim)
        if self._recording:
            raw = pygame.image.tostring(self.screen, 'RGB')
            w, h = self.screen.get_size()
            self._frames.append(Image.frombytes('RGB', (w, h), raw))

    # ── private ───────────────────────────────────────────────────────────────

    def _record_trails(self, sim) -> None:
        for body in sim.bodies:
            if body.name == "Sun":
                continue
            last = self._last_record.get(body.name, -self.trail_interval)
            if sim.t - last < self.trail_interval:
                continue
            trail = self._trails.setdefault(body.name, deque(maxlen=self.TRAIL_LEN))
            trail.append((body.position.copy(), body.color))
            self._last_record[body.name] = sim.t

    def _draw_grid(self) -> None:
        for r in GRID_RADII:
            pts = []
            chunks = 144
            for i in range(chunks):
                a = 2 * np.pi * i / chunks
                res = self.camera.project(np.array([r*np.cos(a), r*np.sin(a), 0.]))
                if res:
                    pts.append((int(res[0]), int(res[1])))
            for i in range(0, len(pts)-1, 2):
                pygame.draw.line(self.screen, COLOR_GRID, pts[i], pts[i+1], 1)

    def _draw_trails(self) -> None:
        for name, trail in self._trails.items():
            n = len(trail)
            for i, (pos, color) in enumerate(trail):
                res = self.camera.project(pos)
                if res is None:
                    continue
                frac = i / max(n-1, 1)
                c = tuple(int(ch * frac * TRAIL_FADE) for ch in color)
                pygame.draw.circle(self.screen, c, (int(res[0]), int(res[1])), 1)

    def _draw_bodies(self, sim) -> None:
        order = [(self.camera.project(b.position)[2], b)
                 for b in sim.bodies if self.camera.project(b.position)]
        order.sort(key=lambda x: -x[0])
        for _, body in order:
            if body.name == "Sun":
                self._draw_emissive(body)
            else:
                self._draw_shaded_sphere(body, sim.sun.position)
                if getattr(body, 'tilt', 0.0) != 0.0:
                    self._draw_axis(body)

    def _draw_axis(self, body) -> None:
        sx, sy, sr = self.camera.project_radius(body.position, body.radius)
        if sr is None or sr < 0.5:
            return
        right, up, _ = self.camera.basis()
        k   = np.array([np.sin(body.tilt), 0.0, np.cos(body.tilt)])
        # Use the same screen-space (orthographic) formula as the sphere shader:
        # the pole where N_w = k appears at offset (dot(k,right)*sr, -dot(k,up)*sr)
        # from the projected sphere centre. True perspective projection of the 3D
        # pole diverges from this when the sphere is zoomed in or off-centre.
        kx  = float(np.dot(k, right))
        ky  = float(np.dot(k, up))
        ext = 2.5   # cap extension as a multiple of the sphere radius
        np_x = int(round(sx + kx * sr));        np_y = int(round(sy - ky * sr))
        sp_x = int(round(sx - kx * sr));        sp_y = int(round(sy + ky * sr))
        nc_x = int(round(sx + kx * sr * ext));  nc_y = int(round(sy - ky * sr * ext))
        sc_x = int(round(sx - kx * sr * ext));  sc_y = int(round(sy + ky * sr * ext))
        pygame.draw.line(self.screen, COLOR_AXIS, (np_x, np_y), (nc_x, nc_y), 1)
        pygame.draw.line(self.screen, COLOR_AXIS, (sp_x, sp_y), (sc_x, sc_y), 1)

    def _draw_emissive(self, body) -> None:
        sx, sy, sr = self.camera.project_radius(body.position, body.radius)
        if sr is None or sr < 0.5:
            return
        for scale, alpha in SUN_GLOW_LAYERS:
            gr = int(sr * scale) + 1
            s  = pygame.Surface((gr*2+2, gr*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*body.color, alpha), (gr+1, gr+1), gr)
            self.screen.blit(s, (int(sx)-gr-1, int(sy)-gr-1))
        pygame.draw.circle(self.screen, body.color, (int(sx), int(sy)), max(1, int(sr)))

    def _draw_shaded_sphere(self, body, light_pos: np.ndarray) -> None:
        sx, sy, sr = self.camera.project_radius(body.position, body.radius)
        if sr is None or sr < 0.5:
            return

        cx, cy = int(round(sx)), int(round(sy))
        r  = int(sr) + 1
        SW, SH = self.screen.get_size()
        x0, x1 = max(0, cx-r), min(SW, cx+r+1)
        y0, y1 = max(0, cy-r), min(SH, cy+r+1)
        if x0 >= x1 or y0 >= y1:
            return

        pw, ph = x1-x0, y1-y0

        # Normal components in camera space (ph×pw arrays)
        dx = np.arange(x0, x1, dtype=np.float32) - sx
        dy = -(np.arange(y0, y1, dtype=np.float32) - sy)  # flip screen-y
        DX, DY = np.meshgrid(dx, dy)

        nx    = DX / sr
        ny    = DY / sr
        nz_sq = 1.0 - nx**2 - ny**2
        mask  = nz_sq >= 0.0
        nz    = np.sqrt(np.where(mask, nz_sq, 0.0))

        # Light direction in camera space.
        # The visible-hemisphere normal is (nx, ny, -nz) in (right, up, fwd) coords,
        # so diffuse = nx*lx + ny*ly - nz*lz.
        right, up, fwd = self.camera.basis()
        lv = light_pos - body.position
        lv = lv / max(np.linalg.norm(lv), 1e-9)
        lx, ly, lz = np.dot(lv, right), np.dot(lv, up), np.dot(lv, fwd)

        diffuse_raw = nx*lx + ny*ly - nz*lz
        t = np.clip((diffuse_raw + TERMINATOR_WIDTH) / (2.0 * TERMINATOR_WIDTH), 0.0, 1.0)
        diffuse = t * t * (3.0 - 2.0 * t)          # smoothstep terminator
        diffuse = diffuse ** DIFFUSE_GAMMA           # power curve for natural falloff
        intensity = np.where(mask, AMBIENT + DIFFUSE * diffuse, 0.0)

        if getattr(body, 'rotation', 0.0) != 0.0:
            # World-space normal from camera-space components
            N_wx = nx*right[0] + ny*up[0] - nz*fwd[0]
            N_wy = nx*right[1] + ny*up[1] - nz*fwd[1]
            N_wz = nx*right[2] + ny*up[2] - nz*fwd[2]
            # Project onto equatorial basis of the tilted axis:
            #   k = [sin(tilt), 0, cos(tilt)]
            #   e1 = [cos(tilt), 0, -sin(tilt)]   (perp to k in XZ plane)
            #   e2 = [0, 1, 0]                     (world Y)
            st_t = np.sin(body.tilt);  ct_t = np.cos(body.tilt)
            lon  = np.arctan2(N_wy, N_wx*ct_t - N_wz*st_t) - body.rotation
            seg = 2 * np.pi / LONGITUDE_COUNT
            lon_frac = (lon % seg) / seg
            lon_mask = (lon_frac < LONGITUDE_HALF_WIDTH) | (lon_frac > 1.0 - LONGITUDE_HALF_WIDTH)

        R = np.clip(body.color[0] * intensity, 0, 255).astype(np.uint8)
        G = np.clip(body.color[1] * intensity, 0, 255).astype(np.uint8)
        B = np.clip(body.color[2] * intensity, 0, 255).astype(np.uint8)

        if getattr(body, 'rotation', 0.0) != 0.0:
            line_px = mask & lon_mask
            R = np.where(line_px, np.clip(COLOR_LONGITUDE[0] * intensity, 0, 255), R).astype(np.uint8)
            G = np.where(line_px, np.clip(COLOR_LONGITUDE[1] * intensity, 0, 255), G).astype(np.uint8)
            B = np.where(line_px, np.clip(COLOR_LONGITUDE[2] * intensity, 0, 255), B).astype(np.uint8)
        A = np.where(mask, 255, 0).astype(np.uint8)

        # surfarray is (width, height) → transpose from (ph,pw)
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        p3   = pygame.surfarray.pixels3d(surf)
        pa   = pygame.surfarray.pixels_alpha(surf)
        p3[:,:,0] = R.T;  p3[:,:,1] = G.T;  p3[:,:,2] = B.T
        pa[:,:] = A.T
        del p3, pa

        self.screen.blit(surf, (x0, y0))

    def _draw_hud(self, sim, paused: bool) -> None:
        # Top-left: sim time + controls
        status = "PAUSED" if paused else f"day {sim.t:.1f}"
        lines = [
            status,
            "WASD / arrows : orbit camera",
            "+  /  -       : zoom",
            "Space         : pause / resume",
            ",  /  .       : -1 / +1 day per second",
            "[  /  ]       : trail interval",
            "c             : cycle coordinates",
            "r             : record gif",
        ]
        for i, txt in enumerate(lines):
            self.screen.blit(self._font.render(txt, True, COLOR_HUD), (10, 10 + i*17))

        # Top-right: speed, zoom, trail interval
        if self._sim_speed_hours < 24:
            h = self._sim_speed_hours
            speed_txt = f"{h} {'hr' if h == 1 else 'hrs'}/s"
        else:
            d = self._sim_speed_hours // 24
            speed_txt = f"{d} {'day' if d == 1 else 'days'}/s"
        zoom_txt  = f"zoom: {self.camera.distance:.0f}"
        trail_txt = f"trail: {self._format_interval(self.trail_interval)}"
        top_right = [
            (speed_txt, COLOR_SPEED),
            (zoom_txt,  COLOR_SPEED),
            (trail_txt, COLOR_HUD),
        ]
        if self._recording:
            top_right.insert(0, ("● REC", (220, 50, 50)))
        for i, (txt, color) in enumerate(top_right):
            surf = self._font.render(txt, True, color)
            self.screen.blit(surf, (self.screen.get_width() - surf.get_width() - 10, 10 + i*17))

    @staticmethod
    def _format_interval(days: float) -> str:
        if days < 1:
            hours = round(days * 24)
            return f"{hours} hr" if hours == 1 else f"{hours} hrs"
        elif days < 7:
            d = round(days)
            return f"{d} day" if d == 1 else f"{d} days"
        elif days < 28:
            w = round(days / 7)
            return f"{w} week" if w == 1 else f"{w} weeks"
        else:
            m = round(days / 30)
            return f"{m} month" if m == 1 else f"{m} months"

    # ── moon phase ────────────────────────────────────────────────────────────

    def _compute_phase(self, sim) -> tuple:
        """Return (phase_angle 0–2π, phase_index 0–7, within_phase_fraction 0–1).

        Phase angle is the angle of the Moon relative to the Sun as seen from
        Earth, measured in the XY plane (works for the placeholder flat orbits;
        for tilted orbits you'd project onto the invariant plane instead).
        """
        e2s = sim.sun.position  - sim.earth.position
        e2m = sim.moon.position - sim.earth.position
        phi = (np.arctan2(e2m[1], e2m[0]) - np.arctan2(e2s[1], e2s[0])) % (2 * np.pi)
        seg = np.pi / 4          # each of the 8 phases spans 45°
        idx = int(phi / seg) % 8
        return phi, idx, (phi % seg) / seg

    def _moon_ascii(self, phase: float) -> list[str]:
        """5×11 ASCII art of the moon.  '#' = lit, '.' = dark, ' ' = outside."""
        CX, CY  = 5, 2
        waxing  = phase < np.pi
        cos_phi = np.cos(phase)
        art = []
        for r in range(5):
            y = (r - CY) / 2.5        # aspect-corrected y (chars ~2.5× taller than wide)
            row = []
            for c in range(11):
                x = (c - CX) / float(CX)   # x normalised –1 to +1
                if x*x + y*y > 1.05:
                    row.append(' ')
                else:
                    lit = (x >= cos_phi) if waxing else (x <= -cos_phi)
                    row.append('#' if lit else '.')
            art.append(''.join(row))
        return art

    @staticmethod
    def _phase_bar(frac: float) -> str:
        """4-cell progress bar with half-steps: [|>--] etc."""
        n     = int(frac * 8)      # 0–8 half-steps
        full  = n // 2
        half  = n % 2
        empty = 4 - full - half
        return '[' + '|' * full + ('>' if half else '') + '-' * empty + ']'

    def _draw_moon_phase(self, sim) -> None:
        phase, idx, frac = self._compute_phase(sim)
        art   = self._moon_ascii(phase)
        name  = self._PHASE_NAMES[idx]
        cycle = '  '.join('*' if i == idx else 'o' for i in range(8))
        bar   = self._phase_bar(frac)

        lines = art + ['', name, cycle, bar]
        surfs = [self._font.render(l if l else ' ', True, COLOR_MOON_PHASE) for l in lines]

        max_w  = max(s.get_width() for s in surfs)
        sw, sh = self.screen.get_size()
        x0     = sw - max_w - 10
        y0     = sh - len(lines) * 17 - 10

        for i, surf in enumerate(surfs):
            # right-align each line within the block
            self.screen.blit(surf, (x0 + max_w - surf.get_width(), y0 + i * 17))

    def _draw_coords(self, sim) -> None:
        MODES = ["cartesian", "cylindrical", "spherical"]
        mode  = MODES[self._coord_mode]

        lines = [f"coords : {mode}", ""]
        for body in (sim.earth, sim.moon):
            x, y, z = body.position
            lines.append(body.name.upper())
            if mode == "cartesian":
                lines.append(f"  x = {x:>10.3f}")
                lines.append(f"  y = {y:>10.3f}")
                lines.append(f"  z = {z:>10.3f}")
            elif mode == "cylindrical":
                rho = np.sqrt(x**2 + y**2)
                phi = np.degrees(np.arctan2(y, x)) % 360
                lines.append(f"  rho = {rho:>8.3f}")
                lines.append(f"  phi = {phi:>8.3f} deg")
                lines.append(f"  z   = {z:>8.3f}")
            elif mode == "spherical":
                r     = np.sqrt(x**2 + y**2 + z**2)
                theta = np.degrees(np.arctan2(np.sqrt(x**2 + y**2), z))
                phi   = np.degrees(np.arctan2(y, x)) % 360
                lines.append(f"  r     = {r:>7.3f}")
                lines.append(f"  theta = {theta:>7.3f} deg")
                lines.append(f"  phi   = {phi:>7.3f} deg")
            lines.append("")

        sh = self.screen.get_height()
        for i, txt in enumerate(reversed(lines)):
            surf = self._font.render(txt, True, COLOR_COORDS)
            self.screen.blit(surf, (10, sh - 10 - (i + 1) * 17))
