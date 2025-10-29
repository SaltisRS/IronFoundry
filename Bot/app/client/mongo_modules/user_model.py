from typing import TypedDict


class UserModel(TypedDict):
    _id: int
    rsn: str = None
    rank: int = None
    donations: int = 0
    event_winnings: int = 0
    loot_value: int = 0
    last_seen: int = 0
    alts: list[dict[str, str]] = []
    pk_kills: int = 0
    pk_deaths: int = 0
    pk_kd: int = 0
    pk_gained: int = 0
    pk_lost: int = 0
    known_names: list[str] = []
    hof_ref: str = None
    individual_permissions: dict[str, bool] = {}
    tags: list[dict[str, bool]] = []
    incidents: dict[dict[str, str]] = {}
