# ✨ CSim ✨

A real-time 3D solar system simulation built with Python and pygame. 
🌍🌕🌟

## To Do
- [Issue] Drawn axis and drawn longitude lines don't seem to be coaxial
- different cameras (instead of orbital, controls xyz + yaw + roll)
- display day and night on earth
  - poles, where equator meets prime meridian, eventuall specific places
- Add an earth view camera like a picture in picture
  - start with fixed perspective of north pole looking up
  - add toggle to south, maybe use the same locations where we display day and night
  - eventually allow tilting of earth view
- more user config
  - trail fade duration
  - earth/sun distance
  - moon/earh distance
  - earth radius
  - moon radius

## Features

- Circular orbit of Earth around Sun and Moon around Earth
- Diffuse shading from the Sun with ambient light
- Earth axial tilt (23.5°) with 8 rotating longitude lines
- Rotation axis visualization
- Fading orbital trail history
- Moon phase tracker with ASCII art and phase name
- Orbit camera — orbit, zoom, pan
- Adjustable simulation speed (1 hr/s up to N days/s)
- Coordinate display (Cartesian / Cylindrical / Spherical)

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
  sim.py      # Simulation state and orbital mechanics
  render.py   # 3D renderer, camera, shading, HUD
  main.py     # Event loop
```
