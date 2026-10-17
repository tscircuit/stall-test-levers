"""Regenerate the printable parts and STEP models from their build123d sources."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

for source in (
    "models/nema17/nema17_stall_lever.py",
    "models/nema23/nema23_stall_lever.py",
    "models/nema34/nema34_stall_lever.py",
    "models/nema34/nema34_printed_key.py",
):
    subprocess.run([sys.executable, str(ROOT / source)], check=True)
