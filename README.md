# ✨ CSim ✨

A real-time 3D solar system simulation built with Python and pygame.
🌍🌕🌟

![CSim demo](recording_20260308_010004recording_00_01_00.gif)
## Features

- Circular orbit of Earth around Sun and Moon around Earth
- Moon orbital tilt (5.1°) relative to the ecliptic
- Diffuse shading with smoothstep terminator and natural solar falloff
- Earth axial tilt (23.5°) with 4 jade green rotating longitude lines
- Rotation axis coaxial with longitude line convergence
- Fading orbital trail history
- Moon phase tracker with ASCII art and phase name
- Orbit camera — orbit, zoom, pan
- Adjustable simulation speed (1 hr/s up to N days/s)
- Coordinate display (Cartesian / Cylindrical / Spherical)
- GIF recording
- Single config file for all simulation and display parameters

## Controls

| Key | Action |
|-----|--------|
| `W/S` or `↑/↓` | Orbit camera up/down |
| `A/D` or `←/→` | Orbit camera left/right |
| `+` / `-` | Zoom in / out |
| `Space` | Pause / resume |
| `,` / `.` | Decrease / increase sim speed |
| `[` / `]` | Trail interval shorter / longer |
| `C` | Cycle coordinate display mode |
| `R` | Start / stop GIF recording |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Structure

```
csim/
  config.py   # All simulation and display parameters
  sim.py      # Simulation state and orbital mechanics
  render.py   # 3D renderer, camera, shading, HUD
  main.py     # Event loop
```

## To Do

- Moon ascending node precession — the ascending node (where the Moon crosses
  the ecliptic northward) precesses once every 18.6 years; currently fixed on
  the X-axis
- Different cameras — free-fly with xyz + yaw + roll instead of orbital
- Display day/night on Earth — poles, equator/prime meridian intersection,
  eventually specific locations
- Earth view camera — picture-in-picture from north pole looking up, with
  toggle to south pole
