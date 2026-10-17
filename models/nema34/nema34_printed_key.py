"""Build123d key for fit checking the NEMA34 lever; not load rated.

Nominal key size is 5 x 5 x 20 mm. Cross-section reduced to 4.9 mm
for printing clearance. Use a steel key for powered stall tests.
"""
from pathlib import Path
import json
from build123d import Box, Align, chamfer, export_stl, export_step

NOMINAL_SIZE = 5.0
TOTAL_CLEARANCE = 0.10
LENGTH = 20.0
EDGE_CHAMFER = 0.20
OUT = Path(__file__).resolve().parent

key = Box(LENGTH, NOMINAL_SIZE-TOTAL_CLEARANCE,
          NOMINAL_SIZE-TOTAL_CLEARANCE,
          align=(Align.CENTER, Align.CENTER, Align.MIN))
key = chamfer(key.edges(), length=EDGE_CHAMFER)
key.label = "NEMA34 printed key - fit check only"
assert key.is_valid and len(key.solids()) == 1
export_step(key, OUT / "nema34_printed_key.step")
assert export_stl(key, OUT / "nema34_printed_key.stl")
print(json.dumps(dict(valid=key.is_valid, solids=len(key.solids()),
                     dimensions_mm=list(key.bounding_box().size))))
