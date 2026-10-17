"""Parametric build123d stall-test lever. Dimensions are millimetres.

Run: python nema23_stall_lever.py
Requires: build123d==0.13.0. Files export beside this script.
The 8 mm / 7.5 mm D-shaft dimensions are ASSUMPTIONS: check fit first.
"""
from pathlib import Path
from math import sqrt
import json
from build123d import *

# Change these two measured shaft dimensions to match your motor.
SHAFT_DIAMETER = 8.0
SHAFT_ACROSS_D = 7.5  # Flat face to opposite circular edge.
RADIAL_CLEARANCE = 0.15  # 0.30 mm added to diameter AND across-D.
LEVER_RADIUS = 150.0  # Shaft axis to end-hole centre.
ARM_THICKNESS = 12.0
TIP_WIDTH = 24.0
ROOT_WIDTH = 36.0
HUB_DIAMETER = 36.0
HUB_HEIGHT = 22.0
END_HOLE_DIAMETER = 6.5
SET_SCREW_CLEARANCE = 5.6  # M5 screw; actual threads are in captive metal nut.
SET_SCREW_Z = 11.0
NUT_AF = 8.0  # Standard full-height M5 hex nut, 8 mm across flats, ~4 mm thick.
NUT_SLOT_WIDTH = 8.3
NUT_SLOT_THICKNESS = 4.5
NUT_CENTRE_Y = 11.5
OUT = Path(__file__).resolve().parent


def d_profile(clearance=RADIAL_CLEARANCE):
    """Offset both the curved wall and flat outward by radial clearance."""
    radius = SHAFT_DIAMETER / 2 + clearance
    flat_y = SHAFT_ACROSS_D - SHAFT_DIAMETER / 2 + clearance
    disk = Circle(radius)
    lower_half_plane = Pos(0, (flat_y - 50) / 2) * Rectangle(100, 50 + flat_y)
    return disk & lower_half_plane


def d_socket(height):
    return extrude(d_profile(), amount=height)


def make_lever():
    assert SHAFT_DIAMETER / 2 < SHAFT_ACROSS_D < SHAFT_DIAMETER
    assert LEVER_RADIUS > HUB_DIAMETER + TIP_WIDTH
    # Broad, tapered root blends tangentially into the round hub and tip.
    r0, r1 = ROOT_WIDTH / 2, TIP_WIDTH / 2
    slope = (r0 - r1) / LEVER_RADIUS
    nx, ny = slope, sqrt(1 - slope * slope)
    outline = Polygon((r0*nx, -r0*ny),
                      (LEVER_RADIUS+r1*nx, -r1*ny),
                      (LEVER_RADIUS+r1*nx, r1*ny),
                      (r0*nx, r0*ny), align=None)
    outline = outline + Circle(r0) + Pos(LEVER_RADIUS, 0) * Circle(r1)
    body = extrude(outline, amount=ARM_THICKNESS)
    body += Cylinder(HUB_DIAMETER/2, HUB_HEIGHT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(0, 0, -1) * d_socket(HUB_HEIGHT + 2)
    # A small lead-in on both ends of the socket aids installation.
    for z0, z1, c0, c1 in [(0, 0.5, RADIAL_CLEARANCE+0.5, RADIAL_CLEARANCE),
                            (HUB_HEIGHT-0.5, HUB_HEIGHT, RADIAL_CLEARANCE, RADIAL_CLEARANCE+0.5)]:
        body -= loft([Pos(0,0,z0)*d_profile(c0), Pos(0,0,z1)*d_profile(c1)])
    body -= Pos(LEVER_RADIUS, 0, -1) * Cylinder(END_HOLE_DIAMETER/2,
                ARM_THICKNESS+2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Radial screw points inward onto the D flat (+Y).
    body -= Pos(0, 16, SET_SCREW_Z) * Rot(90, 0, 0) * Cylinder(
        SET_SCREW_CLEARANCE/2, 32)
    # Top-loading nut pocket: a V seat locates a point-down hex nut.
    # This provides a metal M5 thread without tapping printed plastic.
    half = NUT_SLOT_WIDTH / 2
    bottom = SET_SCREW_Z - NUT_AF/sqrt(3)
    side_bottom = bottom + half/sqrt(3)
    slot_profile = Plane.XZ * Polygon(
        (0,bottom), (half,side_bottom), (half,HUB_HEIGHT+1),
        (-half,HUB_HEIGHT+1), (-half,side_bottom), align=None)
    pocket = extrude(slot_profile, amount=NUT_SLOT_THICKNESS)
    body -= Pos(0,NUT_CENTRE_Y+NUT_SLOT_THICKNESS/2,0) * pocket
    body.label = "NEMA23 stall lever - assumed 8mm D shaft"
    return body


def main():
    lever = make_lever()
    coupon = Cylinder(13, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    coupon -= Pos(0,0,-1) * d_socket(8)
    for name, shape in [("nema23_stall_lever", lever), ("shaft_fit_coupon", coupon)]:
        assert shape.is_valid and len(shape.solids()) == 1
        export_step(shape, OUT / f"{name}.step")
        assert export_stl(shape, OUT / f"{name}.stl", tolerance=0.025, angular_tolerance=0.08)
    report = dict(valid=lever.is_valid, solids=len(lever.solids()),
                  volume_mm3=lever.volume,
                  bounding_box_mm=list(lever.bounding_box().size),
                  shaft_nominal_mm=SHAFT_DIAMETER,
                  shaft_across_D_nominal_mm=SHAFT_ACROSS_D,
                  bore_diameter_mm=SHAFT_DIAMETER+2*RADIAL_CLEARANCE,
                  bore_across_D_mm=SHAFT_ACROSS_D+2*RADIAL_CLEARANCE,
                  effective_lever_mm=LEVER_RADIUS)
    (OUT / "geometry_check.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
