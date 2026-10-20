"""The one time format used in labels, the transcript and the CLI: `mm:ss.s`."""


def mmss(t: float) -> str:
    minutes, seconds = divmod(t, 60)
    return f"{int(minutes):02d}:{seconds:04.1f}"
