"""Birth-moment parsing: local civil time -> UTC -> Julian day (UT).

Accepts an IANA zone (historical DST / war time handled by tzdata) or an
explicit UTC offset. Ambiguous and non-existent local times are reported, not
silently guessed."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import swisseph as swe

GENDERS = {"male", "female", "other", "unspecified"}


@dataclass
class Birth:
    local: datetime            # tz-aware local civil time
    utc: datetime              # tz-aware UTC
    jd_ut: float
    lat: float
    lon: float
    alt: float
    gender: str
    place: str
    name: str
    tz_source: str             # 'iana:<zone>' or 'offset'
    utc_offset_hours: float
    warnings: list = field(default_factory=list)

    @property
    def lmt_offset_hours(self):
        return self.lon / 15.0

    def as_dict(self):
        return {
            "name": self.name, "place": self.place, "gender": self.gender,
            "local_time": self.local.isoformat(), "utc_time": self.utc.isoformat(),
            "julian_day_ut": self.jd_ut, "utc_offset_hours": self.utc_offset_hours,
            "timezone_source": self.tz_source,
            "local_mean_time": (self.utc + timedelta(hours=self.lmt_offset_hours)
                                ).replace(tzinfo=None).isoformat(),
            "latitude": self.lat, "longitude": self.lon, "altitude_m": self.alt,
            "delta_t_seconds": swe.deltat(self.jd_ut) * 86400.0,
            "warnings": list(self.warnings),
        }


def jd_from_utc(dt):
    dt = dt.astimezone(timezone.utc)
    h = dt.hour + dt.minute / 60.0 + (dt.second + dt.microsecond / 1e6) / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, h, swe.GREG_CAL)


def utc_from_jd(jd):
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(microseconds=round(h * 3600e6))


def _parse_time(s):
    parts = [p for p in str(s).strip().split(":")]
    if not 2 <= len(parts) <= 3:
        raise ValueError(f"time must be HH:MM or HH:MM:SS, got {s!r}")
    hh, mm = int(parts[0]), int(parts[1])
    sec = float(parts[2]) if len(parts) == 3 else 0.0
    if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= sec < 60):
        raise ValueError(f"time out of range: {s!r}")
    return hh, mm, sec


def parse_birth(data):
    """data: dict. New keys: date 'YYYY-MM-DD', time 'HH:MM[:SS]', timezone
    (IANA) or tz_offset (hours), lat, lon, [alt], [gender], [place], [name].
    Legacy keys y/mo/d/hh/mm[/ss]/tz_offset are also accepted."""
    d = dict(data)
    warnings = []
    if "date" in d:
        y, mo, dd = (int(x) for x in str(d["date"]).split("-"))
        hh, mi, sec = _parse_time(d.get("time", "12:00"))
        if "time" not in d:
            warnings.append("no birth time given: 12:00 assumed; lagna, houses and "
                            "everything time-sensitive is unreliable")
    else:
        y, mo, dd = int(d["y"]), int(d["mo"]), int(d["d"])
        hh, mi, sec = int(d["hh"]), int(d["mm"]), float(d.get("ss", 0))

    lat, lon = float(d["lat"]), float(d["lon"])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("lat must be in [-90, 90] and lon in [-180, 180]")
    alt = float(d.get("alt", 0.0))
    gender = str(d.get("gender", "unspecified")).lower()
    if gender not in GENDERS:
        raise ValueError(f"gender must be one of {sorted(GENDERS)}")

    whole = int(sec)
    micro = int(round((sec - whole) * 1e6))
    naive = datetime(y, mo, dd, hh, mi, whole, micro)

    if d.get("timezone"):
        zname = d["timezone"]
        try:
            zone = ZoneInfo(zname)
        except ZoneInfoNotFoundError:
            raise ValueError(f"unknown IANA timezone {zname!r}")
        local = naive.replace(tzinfo=zone, fold=int(d.get("fold", 0)))
        # Non-existent (spring-forward gap): round-trip through UTC changes it.
        back = local.astimezone(timezone.utc).astimezone(zone)
        alt_local = naive.replace(tzinfo=zone, fold=1 - local.fold)
        if back.replace(tzinfo=None) != naive:
            warnings.append(f"local time {naive} does not exist in {zname} (DST gap); "
                            f"interpreted as {back.isoformat()}")
        elif alt_local.utcoffset() != local.utcoffset():
            # Ambiguous (fall-back overlap): both folds are real instants.
            off = lambda x: x.utcoffset().total_seconds() / 3600.0
            warnings.append(f"local time {naive} is ambiguous in {zname} (DST overlap); "
                            f"fold={local.fold} used (UTC{off(local):+g}); pass "
                            f"'fold': {1 - local.fold} for UTC{off(alt_local):+g}")
        if "tz_offset" in d:
            given = float(d["tz_offset"])
            real = local.utcoffset().total_seconds() / 3600.0
            if abs(given - real) > 1e-9:
                warnings.append(f"tz_offset {given} disagrees with {zname} on that date "
                                f"({real}); the IANA zone was used")
        tz_source = f"iana:{zname}"
    elif "tz_offset" in d:
        off = float(d["tz_offset"])
        if not -14 <= off <= 14:
            raise ValueError("tz_offset must be within [-14, 14] hours")
        local = naive.replace(tzinfo=timezone(timedelta(hours=off)))
        tz_source = "offset"
        warnings.append("fixed UTC offset given: historical DST/war-time is NOT applied; "
                        "pass an IANA 'timezone' to have it checked")
    else:
        raise ValueError("either 'timezone' (IANA name) or 'tz_offset' is required")

    utc = local.astimezone(timezone.utc)
    return Birth(local=local, utc=utc, jd_ut=jd_from_utc(utc), lat=lat, lon=lon, alt=alt,
                 gender=gender, place=str(d.get("place", "")), name=str(d.get("name", "")),
                 tz_source=tz_source,
                 utc_offset_hours=local.utcoffset().total_seconds() / 3600.0,
                 warnings=warnings)


def to_local(jd, tzinfo):
    """Julian day (UT) -> aware datetime in the birth's zone."""
    return utc_from_jd(jd).astimezone(tzinfo)


def iso(jd, tzinfo):
    return to_local(jd, tzinfo).isoformat(timespec="seconds")
