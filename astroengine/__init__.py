"""astroengine - sidereal (Vedic) astrology calculation engine on Swiss Ephemeris.

    from astroengine import compute, Config
    data = compute({"date": "1990-01-01", "time": "12:00", "timezone": "Asia/Kolkata",
                    "lat": 28.6139, "lon": 77.209})
"""
from .config import Config, DEFAULT
from .compute import compute, ENGINE_VERSION

__all__ = ["compute", "Config", "DEFAULT", "ENGINE_VERSION"]
