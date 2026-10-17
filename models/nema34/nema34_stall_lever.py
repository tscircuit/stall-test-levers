"""Parametric build123d stall-test lever. Dimensions are millimetres.

Run: python nema34_stall_lever.py
Requires: build123d==0.13.0. Files export beside this script.
For 34HS31-6004S1: 14 mm keyed shaft, separate 5 x 5 mm steel key.
Print the coupon first; verify the actual key and shaft before loading.
"""
from pathlib import Path
from math import sqrt
import json
from build123d import *

# Shaft and key dimensions; the steel key is separate hardware.
SHAFT_DIAMETER = 14.0
KEY_WIDTH = 5.0
KEY_HEIGHT = 5.0
KEY_LENGTH = 20.0
KEY_TOP_FROM_AXIS = 9.0  # Drawing: 16 mm from opposite shaft edge to key top.
KEY_SIDE_CLEARANCE = 0.10
KEY_TOP_CLEARANCE = 0.20
RADIAL_CLEARANCE = 0.15  # 0.30 mm added to shaft diameter.
LEVER_RADIUS = 150.0  # Shaft axis to end-hole centre.
ARM_THICKNESS = 16.0
TIP_WIDTH = 28.0
ROOT_WIDTH = 44.0
HUB_DIAMETER = 44.0
HUB_HEIGHT = 26.0
END_HOLE_DIAMETER = 6.5
SET_SCREW_CLEARANCE = 5.6  # M5 screw; actual threads are in captive metal nut.
SET_SCREW_Z = 13.0
NUT_AF = 8.0  # Standard full-height M5 hex nut, 8 mm across flats, ~4 mm thick.
NUT_SLOT_WIDTH = 8.3
NUT_SLOT_THICKNESS = 4.5
NUT_CENTRE_Y = 15.0
OUT = Path(__file__).resolve().parent


def bore_profile(clearance=RADIAL_CLEARANCE):
    radius = SHAFT_DIAMETER / 2 + clearance
    width = KEY_WIDTH + 2 * KEY_SIDE_CLEARANCE
    top = KEY_TOP_FROM_AXIS + KEY_TOP_CLEARANCE
    # The shaft has a groove; the hub has a matching groove on the same side.
    # A separate steel key bridges the two grooves and carries torque.
    keyway = Pos(0, top/2) * Rectangle(width, top)
    return Circle(radius) + keyway


def socket(height):
    return extrude(bore_profile(), amount=height)


def make_lever():
    assert KEY_TOP_FROM_AXIS > SHAFT_DIAMETER / 2
    assert KEY_LENGTH <= HUB_HEIGHT
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
    body -= Pos(0, 0, -1) * socket(HUB_HEIGHT + 2)
    # A small lead-in on both ends of the socket aids installation.
    for z0, z1, c0, c1 in [(0, 0.5, RADIAL_CLEARANCE+0.5, RADIAL_CLEARANCE),
                            (HUB_HEIGHT-0.5, HUB_HEIGHT, RADIAL_CLEARANCE, RADIAL_CLEARANCE+0.5)]:
        body -= loft([Pos(0,0,z0)*bore_profile(c0), Pos(0,0,z1)*bore_profile(c1)])
    body -= Pos(LEVER_RADIUS, 0, -1) * Cylinder(END_HOLE_DIAMETER/2,
                ARM_THICKNESS+2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Radial screw points inward onto the steel key (+Y).
    body -= Pos(0, 24, SET_SCREW_Z) * Rot(90, 0, 0) * Cylinder(
        SET_SCREW_CLEARANCE/2, 48)
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
    body.label = "NEMA34 stall lever - 14mm keyed shaft - 34HS31-6004S1"
    return body


def main():
    lever = make_lever()
    coupon = Cylinder(17, 6, align=(Align.CENTER, Align.CENTER, Align.MIN))
    coupon -= Pos(0,0,-1) * socket(8)
    for name, shape in [("nema34_stall_lever", lever), ("nema34_shaft_fit_coupon", coupon)]:
        assert shape.is_valid and len(shape.solids()) == 1
        export_step(shape, OUT / f"{name}.step")
        assert export_stl(shape, OUT / f"{name}.stl", tolerance=0.025, angular_tolerance=0.08)
    report = dict(valid=lever.is_valid, solids=len(lever.solids()),
                  volume_mm3=lever.volume,
                  bounding_box_mm=list(lever.bounding_box().size),
                  shaft_nominal_mm=SHAFT_DIAMETER,
                  key_width_nominal_mm=KEY_WIDTH,
                  key_height_nominal_mm=KEY_HEIGHT,
                  key_length_recommended_mm=KEY_LENGTH,
                  keyway_width_mm=KEY_WIDTH+2*KEY_SIDE_CLEARANCE,
                  keyway_top_from_axis_mm=KEY_TOP_FROM_AXIS+KEY_TOP_CLEARANCE,
                  bore_diameter_mm=SHAFT_DIAMETER+2*RADIAL_CLEARANCE,
                  rated_holding_torque_Nm=4.8,
                  scale_grams_at_hole_centre=4.8/(LEVER_RADIUS/1000)/9.80665*1000,
                  effective_lever_mm=LEVER_RADIUS)
    (OUT / "geometry_check.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
