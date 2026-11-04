"""Every contested convention in one place. The chosen values are echoed into
the output so a downstream reader always knows which school produced a number."""
from dataclasses import dataclass, asdict, replace


@dataclass(frozen=True)
class Config:
    # Ayanamsa for the Parashari/Jaimini chart. KP always uses its own (kp_ayanamsa).
    ayanamsa: str = "lahiri"            # lahiri | lahiri_icrc | raman | kp | true_chitra | yukteshwar | fagan_bradley
    kp_ayanamsa: str = "kp"             # Krishnamurti ayanamsa, as KP prescribes
    node: str = "mean"                  # mean | true
    include_outer_planets: bool = False # Uranus/Neptune/Pluto (non-classical, reported separately)

    # Dasha year length in days. 365.2425 = Gregorian mean year; classical
    # alternatives are 365.25 (Julian) and 360 (savana).
    dasha_year_days: float = 365.2425

    # Sunrise definition. 'upper_limb_refraction' = visible sunrise used by
    # most modern panchangs; 'disc_centre_no_refraction' = classical Hindu rising.
    sunrise: str = "upper_limb_refraction"

    # Rahu/Ketu special graha drishti: '5_7_9' (common), '7' (BPHS strict: no special aspects).
    node_aspects: str = "5_7_9"
    # Node exaltation: 'taurus_scorpio' (Rahu ex. Taurus) or 'gemini_sagittarius'.
    node_exaltation: str = "taurus_scorpio"

    # Chara karakas: 8 (with Rahu, BPHS) or 7 (Jaimini Sutras as read by many).
    chara_karaka_scheme: int = 8

    # Ephemeris: refuse to run on the Moshier fallback unless this is True.
    allow_moshier: bool = False

    def as_dict(self):
        return asdict(self)

    def with_(self, **kw):
        return replace(self, **kw)


DEFAULT = Config()
