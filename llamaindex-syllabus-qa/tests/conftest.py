import os

# Tracking off before anything imports opik: the callback handler becomes a no-op.
os.environ["OPIK_TRACK_DISABLE"] = "true"
