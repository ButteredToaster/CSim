# CSim — Math Reference

Technical notes on the mathematics underlying each component of the simulation.

---

## Coordinate System

The simulation uses a right-handed world coordinate system:

- **XY plane** — the ecliptic (Earth's orbital plane)
- **Z axis** — north ecliptic pole (up)
- **Origin** — the Sun

All distances are in arbitrary display units. The camera orbits the origin via spherical coordinates (elevation θ, azimuth φ, distance d).

---

## Orbital Mechanics

### Earth's Orbit

A circular orbit in the XY plane with angular velocity ω = 2π / 365.25 rad/day:

```
x(t) = r_e · cos(ω·t)
y(t) = r_e · sin(ω·t)
z(t) = 0
```

### Moon's Orbit

The Moon orbits Earth with angular velocity ω_m = 2π / 27.32 rad/day in a plane inclined 5.1° relative to the ecliptic. The inclination is modelled as a fixed rotation of the orbital plane around the X-axis (fixed ascending node — precession is not yet implemented):

```
x_m = r_m · cos(ω_m · t)
y_m = r_m · sin(ω_m · t) · cos(i)
z_m = r_m · sin(ω_m · t) · sin(i)
```

where i = 5.1°. The Moon's position in world space is `earth.position + [x_m, y_m, z_m]`.

### Earth's Rotation

Earth rotates around its tilt axis at ω_r = 2π / 1.0 rad/day:

```
rotation(t) = ω_r · t  (radians, accumulated)
```

---

## Perspective Projection

The camera basis `(right, up, fwd)` is derived from the spherical coordinates (θ, φ):

```
camera_pos = target + d · [cos(θ)·cos(φ),  cos(θ)·sin(φ),  sin(θ)]
fwd   = normalize(target − camera_pos)
right = normalize(fwd × [0,0,1])       (or fwd × [0,1,0] near the poles)
up    = right × fwd
```

A world point **P** projects to screen coordinates:

```
depth = dot(P − C, fwd)
sx = W/2 + dot(P − C, right) / depth · f
sy = H/2 − dot(P − C, up)   / depth · f
```

where `f = (W/2) / tan(FOV/2)` is the focal length in pixels and `C` is the camera position. The projected screen radius of a sphere with world radius `r` is `sr = r / depth · f`.

---

## Sphere Shading

### Surface Normal (Orthographic Approximation)

For a sphere projected to screen centre `(sx, sy)` with screen radius `sr`, a pixel at `(x, y)` is assigned a surface normal via the screen-space (orthographic) approximation:

```
nx = (x − sx) / sr
ny = −(y − sy) / sr       ← screen Y is flipped
nz = sqrt(1 − nx² − ny²)
```

This treats the sphere as if viewed orthographically — the depth variation across the sphere is ignored. The approximation holds well for small angular size but diverges at close range. Crucially, all surface geometry (longitude lines, axis poles) uses this same approximation for consistency.

The world-space normal is then:

```
N_world = nx·right + ny·up − nz·fwd
```

The minus sign on `nz·fwd` because the visible hemisphere faces the camera (i.e., toward `−fwd`).

### Diffuse Lighting with Soft Terminator

The raw dot product of the surface normal with the light direction (computed in camera space) gives the raw diffuse term. Rather than hard-clipping at zero, a **smoothstep** is applied over a band of half-width `w` straddling the day/night boundary:

```
t = clamp((dot(N, L) + w) / (2w),  0, 1)
diffuse = t² · (3 − 2t)             ← classic smoothstep
diffuse = diffuse ^ γ               ← power curve (γ < 1 brightens highlights)
intensity = ambient + diffuse_weight · diffuse
```

The smoothstep creates a gradual twilight band instead of a hard terminator.

---

## Earth Body Frame and Longitude Lines

### Body-Frame Axes

Earth's axial tilt is modelled as a fixed rotation of the north pole toward +X:

```
k     = [sin(tilt), 0, cos(tilt)]          ← north pole / tilt axis
e1    = [cos(tilt), 0, −sin(tilt)]         ← equatorial direction at lon = 0°  (before rotation)
e2    = [0, 1, 0]                           ← equatorial direction at lon = 90°E (before rotation)
```

Note: `k = e1 × e2`.

After Earth has rotated by angle `θ = body.rotation`:

```
e1_rot = cos(θ)·e1 + sin(θ)·e2  =  [cos(θ)·cos(tilt),   sin(θ),  −cos(θ)·sin(tilt)]
e2_rot = −sin(θ)·e1 + cos(θ)·e2 =  [−sin(θ)·cos(tilt),  cos(θ),   sin(θ)·sin(tilt)]
```

These three vectors `(k, e1_rot, e2_rot)` form an orthonormal basis fixed to Earth's body.

### Longitude from World-Space Normal

Given a world-space surface normal `N`, the body-frame longitude is:

```
lon = atan2(dot(N, e2), dot(N, e1)) − θ
```

This is the angle in the equatorial plane measured from the prime meridian. Longitude lines are rendered by checking whether `lon mod (2π/n)` falls within a small fraction of each segment.

---

## Axis Drawing (Screen-Space Consistency)

The rotation axis is drawn using the **same orthographic approximation** as the sphere shader. The screen position of a pole (where `N_world = ±k`) follows directly from the normal formula:

```
nx_pole = dot(k, right)
ny_pole = dot(k, up)
```

giving screen position `(sx + nx_pole · sr,  sy − ny_pole · sr)`.

Using the true perspective projection of the 3D pole point `body.position ± k·r` instead causes a visible offset when the camera is zoomed in or the sphere is far from the camera's look-at point, because the pole sits at a different depth than the sphere centre, amplifying the parallax.

---

## Observer Location and Sun Elevation

### Zenith Vector

For an observer at geodetic coordinates (lat, lon) on Earth, the local zenith direction in world space is:

```
zenith = sin(lat)·k  +  cos(lat)·cos(lon)·e1_rot  +  cos(lat)·sin(lon)·e2_rot
```

This uses the rotated equatorial basis so the result accounts for both Earth's tilt and its current rotation angle.

### Sun Elevation

The sun elevation angle above the observer's horizon is:

```
elevation = arcsin(dot(zenith, sun_dir))
```

where `sun_dir = normalize(sun.position − earth.position)`. Positive values indicate the sun is above the horizon.

At the north pole (lat = 90°), `zenith = k` regardless of lon or rotation, and elevation ranges between ±tilt over the course of a year.

---

## Moon Phase

The phase angle is measured in the Earth's XY orbital plane as the angle of the Moon relative to the Sun as seen from Earth:

```
φ = atan2(e2m[1], e2m[0]) − atan2(e2s[1], e2s[0])   (mod 2π)
```

where `e2m = moon − earth` and `e2s = sun − earth`. The eight named phases are mapped by dividing the full circle into 45° segments.

---

## Sun Glow

The glow is rendered as a series of `n` concentric alpha-blended circles. Ring scales are distributed with a power curve so that outer rings are spaced farther apart than inner ones:

```
scale(i) = 1 + (m − 1) · (1 − i/(n−1))^s
```

where `m` is the outermost scale multiplier, `s` is the spacing exponent (s = 1 gives even spacing, s > 1 spreads outer rings), and `i` runs from 0 (outermost) to n−1 (disc edge). Alpha ramps quadratically from `a_min` to `a_max` as i increases.
