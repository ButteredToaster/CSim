# TODO

## Axis / Longitude Line Alignment

The rotation axis caps and the longitude line convergence points are still visually
off — they should meet at exactly the same spot on the sphere surface.

Current state: axis is drawn as two cap segments starting from the projected pole
surface points (`body.position ± radius * k`), which is geometrically correct.
The longitude lines converge where `N_world ∥ k`. Mathematically these should
agree, but there's a visible discrepancy that needs further investigation.

Possible causes to explore:
- Camera-space normal reconstruction (`N_wx/N_wy/N_wz`) vs world-space axis direction
- Perspective distortion at off-center viewing angles
- Sign/convention mismatch in the equatorial basis (e1, e2) used for `atan2`

To reproduce: run at low speed, orbit camera to a side view, compare where the
axis caps touch the sphere vs where longitude lines bunch together.
