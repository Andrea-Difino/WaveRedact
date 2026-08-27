
def censor_audio(
    audio_bytes: bytes,
    sample_rate: int,
    channels: int,
    sample_width: int,
    timestamps: list[tuple[float, float]],
    mode: str
) -> bytes:
    """
    Apply censor (silence or beep) manipulatin audio bytes.
    """
    ...