"""Product limits. The browser, the Control API and the Worker read the same values."""

MAX_DURATION_S = 180.0
# Container durations are rarely exact; a 3:00.3 export still counts as three minutes.
DURATION_TOLERANCE_S = 0.5

MAX_FRAMES = 90
FRAME_MAX_SIDE = 1024
FRAME_SAMPLING_STEP_S = 1.0

# The model request as sent over the wire, base64 included.
REQUEST_MAX_BYTES = 16 * 1024 * 1024

MIN_CLAIMS = 3
MAX_CLAIMS = 5
