# csim/config.py — central configuration for the solar system simulation.
# Edit values here to change simulation behaviour, appearance, and controls.
# Runtime editing is not yet supported; restart the sim to apply changes.

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1100
WINDOW_HEIGHT = 700
TARGET_FPS    = 60

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_FOV_DEG   = 55.0
CAMERA_DISTANCE  = 90.0
CAMERA_THETA_DEG = 22.0   # initial elevation angle
CAMERA_PHI_DEG   =  0.0   # initial azimuth angle

# ── Colors ────────────────────────────────────────────────────────────────────
COLOR_SUN        = (255, 220,  50)
COLOR_EARTH      = ( 70, 130, 255)
COLOR_MOON       = (200, 200, 200)
COLOR_AXIS       = (200, 200, 255)
COLOR_LONGITUDE  = (  0, 180, 120)   # jade green
COLOR_GRID       = ( 28,  28,  42)
COLOR_HUD        = (110, 110, 135)
COLOR_SPEED      = (180, 180, 100)
COLOR_COORDS     = (110, 150, 110)
COLOR_MOON_PHASE = (180, 180, 160)

# ── Bodies ────────────────────────────────────────────────────────────────────
SUN_RADIUS    = 4.0
EARTH_RADIUS  = 1.8
MOON_RADIUS   = 0.6

EARTH_ORBITAL_RADIUS = 30.0   # display units, Earth–Sun distance
MOON_ORBITAL_RADIUS  =  4.0   # display units, Moon–Earth distance

EARTH_TILT_DEG        = 23.5  # axial tilt in degrees
MOON_ORBITAL_TILT_DEG = 25.1  # inclination of Moon's orbit relative to the ecliptic (5.1 natural)

EARTH_ORBITAL_PERIOD  = 365.25  # days per orbit around the Sun
MOON_ORBITAL_PERIOD   =  27.32  # days per orbit around Earth
EARTH_ROTATION_PERIOD =   1.0   # days per full rotation

# ── Trails ────────────────────────────────────────────────────────────────────
TRAIL_LEN             = 250
TRAIL_FADE            = 0.4    # max brightness fraction of body color (0–1)
TRAIL_INTERVALS       = [1/24, 0.5, 1, 7, 30]   # days: 1hr, 12hr, 1day, 1week, 1month
TRAIL_INTERVAL_DEFAULT = 2                        # index into TRAIL_INTERVALS

# ── Simulation ────────────────────────────────────────────────────────────────
SIM_SPEED_DEFAULT_HOURS = 24   # hours of sim time per real second

# ── Shading ───────────────────────────────────────────────────────────────────
AMBIENT          = 0.08   # minimum brightness on the night side
DIFFUSE          = 0.92   # contribution of the diffuse (lit) term
TERMINATOR_WIDTH = 0.12   # smoothstep half-width at the day/night boundary
DIFFUSE_GAMMA    = 0.75   # power-curve exponent: <1 brightens highlights

# Sun glow rings painted behind the disc, largest to smallest.
# SUN_GLOW_RADIUS_MULT  : outermost ring radius as a multiple of the disc radius
# SUN_GLOW_STEPS        : number of rings — more = smoother gradient
# SUN_GLOW_ALPHA_MIN/MAX: alpha at the outermost / innermost ring (0–255)
# SUN_GLOW_SPACING      : power exponent controlling ring spacing;
#                         1.0 = even, >1 spreads outer rings farther apart
SUN_GLOW_RADIUS_MULT = 3
SUN_GLOW_STEPS       = 8
SUN_GLOW_ALPHA_MIN   = 6
SUN_GLOW_ALPHA_MAX   = 95
SUN_GLOW_SPACING     = 2.0

def _glow_layers(m: float, n: int, a_min: int, a_max: int, spacing: float) -> list:
    """Generate n glow rings from radius_scale=m down to 1.0 (the disc edge).
    Spacing uses a power curve so outer rings are farther apart than inner ones.
    Alpha ramps quadratically from a_min at the outer edge to a_max at the inner."""
    return [
        (
            round(1.0 + (m - 1.0) * (1.0 - i / (n - 1)) ** spacing, 3),
            int(a_min + (a_max - a_min) * (i / (n - 1)) ** 2),
        )
        for i in range(n)
    ]

SUN_GLOW_LAYERS = _glow_layers(SUN_GLOW_RADIUS_MULT, SUN_GLOW_STEPS, SUN_GLOW_ALPHA_MIN, SUN_GLOW_ALPHA_MAX, SUN_GLOW_SPACING)

# ── Longitude Lines ───────────────────────────────────────────────────────────
LONGITUDE_COUNT      = 4     # number of N–S lines evenly spaced around the globe
LONGITUDE_HALF_WIDTH = 0.05  # fraction of each segment that is colored (0–0.5)

# ── Grid ──────────────────────────────────────────────────────────────────────
GRID_RADII = (30, 60, 120)   # radii of the reference circles in the z=0 plane

# ── Location Panel ────────────────────────────────────────────────────────────
# Observer location on Earth. Eventually supports arbitrary lat/lon.
# Azimuth/elevation of the view direction can be added later;
# North Pole in that system would be (lat=90, lon=0, az=0, el=90).
LOCATION_NAME    = "North Pole"
LOCATION_LAT_DEG =  90.0   # degrees, +N / -S
LOCATION_LON_DEG =   0.0   # degrees, +E / -W
