# CSim

A real-time 3D solar system simulation built with Python and pygame.

```
        .  *        .         *       .          *
   *           .        ___        .        *
          .       ___--   --__            .       *
    *          _-         ##-_     .
          . _-    *    .  ##  -_         .    *
          -    .       . ###   -    .
         -    .    *     ###    -         *
        -   .          . ####   -    .
    .  -_  .    *    .  #####  _-  *         .
    *    --___       . ##### __--      .          *
   .          ---_______---        *        .
        *           .        .         *        .
  .          *            .        .                *
```

## Features

- Circular orbits for Earth and Moon with physically-based periods
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
