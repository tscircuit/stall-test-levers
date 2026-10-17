"""Validate exported CAD, printable meshes, and functional openings.

These checks establish geometry consistency, not physical strength or fit.
"""
from pathlib import Path
import json
from build123d import Align, Box, Cylinder, Pos, Vector, import_step
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]

# Independently check important voids and surrounding material in each export.
FEATURES = {
    "nema17": {
        "shaft_bore_open": ((0, 0, 5), False),
        "D_flat_wall_present": ((0, 2.4, 5), True),
        "radial_screw_passage_open": ((0, 7, 11), False),
        "nut_slot_open": ((0, 11.5, 20), False),
        "nut_slot_side_wall_present": ((5, 11.5, 20), True),
    },
    "nema23": {
        "shaft_bore_open": ((0, 0, 5), False),
        "D_flat_wall_present": ((0, 3.9, 5), True),
        "radial_screw_passage_open": ((0, 7, 11), False),
        "nut_slot_open": ((0, 11.5, 20), False),
        "nut_slot_side_wall_present": ((6, 11.5, 20), True),
    },
    "nema34": {
        "shaft_bore_open": ((0, 0, 5), False),
        "keyway_open": ((0, 8.5, 5), False),
        "keyway_side_wall_present": ((3, 8.5, 5), True),
        "keyway_top_wall_present": ((0, 9.5, 5), True),
        "radial_screw_passage_open": ((0, 11, 13), False),
        "nut_slot_open": ((0, 15, 24), False),
        "nut_slot_side_wall_present": ((5, 15, 24), True),
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_family(family):
    folder = ROOT / "models" / family
    records = {}
    step_paths = sorted(folder.glob("*.step"))
    require(bool(step_paths), f"{family}: no STEP files")
    require({p.stem for p in step_paths} == {p.stem for p in folder.glob('*.stl')},
            f"{family}: STEP and STL filenames differ")
    for path in step_paths:
        cad = import_step(path)
        mesh = trimesh.load_mesh(path.with_suffix(".stl"))
        require(cad.is_valid and len(cad.solids()) == 1, f"{path.name}: invalid solid")
        require(mesh.is_watertight and mesh.is_winding_consistent and
                mesh.volume > 0 and len(mesh.split()) == 1,
                f"{path.name}: invalid mesh")
        bounds = cad.bounding_box()
        require(np.allclose(mesh.bounds, [list(bounds.min), list(bounds.max)], atol=0.03, rtol=0),
                f"{path.name}: mesh and STEP bounds differ")
        require(abs(mesh.volume - cad.volume) / cad.volume < 0.001,
                f"{path.name}: mesh and STEP volumes differ")
        records[path.stem] = {
            "valid_solid": True, "watertight_mesh": True,
            "consistent_winding": True, "connected_meshes": 1,
            "dimensions_mm": list(bounds.size),
        }

    lever = import_step(folder / f"{family}_stall_lever.step")
    features = dict(FEATURES[family])
    features.update({
        "tip_hole_open": ((150, 0, 8), False),
        "arm_solid": ((75, 0, 8), True),
    })
    for name, (point, expected) in features.items():
        require(lever.solids()[0].is_inside(Vector(*point)) == expected,
                f"{family}: {name} failed")

    if family == "nema34":
        # Nominal shaft with 5 mm wide groove, groove floor 4 mm from axis.
        shaft = Cylinder(7, 26, align=(Align.CENTER, Align.CENTER, Align.MIN))
        shaft -= Pos(0, 8, 13) * Box(5, 8, 28)
        steel_key = Pos(0, 6.5, 13) * Box(5, 5, 20)
        for name, part in (("shaft", shaft), ("steel_key", steel_key)):
            overlap = lever & part
            require(overlap is None or overlap.volume < 1e-5,
                    f"{family}: nominal {name} interferes with hub")
        features["nominal_shaft_and_steel_key_clearance"] = True

    report = {"parts": records, "feature_checks": list(features),
              "physical_load_tested": False}
    (folder / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{family}: {len(records)} parts and {len(features)} feature checks passed")


if __name__ == "__main__":
    for family in FEATURES:
        check_family(family)
