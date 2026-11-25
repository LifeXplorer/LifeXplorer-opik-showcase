import os
import sys
import pathlib

# Unit tests never talk to Opik: with tracking disabled, @opik.track and the LangChain
# tracer become no-ops, so the traced functions still run and return normally.
os.environ.setdefault("OPIK_TRACK_DISABLE", "true")
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
