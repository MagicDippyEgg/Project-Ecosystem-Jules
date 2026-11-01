"""Ecological statistics, telemetry tracking, and biodiversity time-series logging."""
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class EcosystemSnapshot:
    tick: int
    total_population: int
    herbivore_count: int
    omnivore_count: int
    carnivore_count: int
    total_biomass: float
    total_vegetation: float
    extinct_species_count: int
    active_species_count: int
    average_speed: float
    average_size: float

class StatsTracker:
    """Records ecological metrics over time for historical analysis and graph rendering."""

    def __init__(self, record_interval: int = 15, max_history_len: int = 400):
        self.record_interval = record_interval
        self.max_history_len = max_history_len
        self.history: List[EcosystemSnapshot] = []
        self.total_births = 0
        self.total_deaths = 0

    def should_record(self, current_tick: int) -> bool:
        return current_tick % self.record_interval == 0

    def record_snapshot(self, snapshot: EcosystemSnapshot) -> None:
        self.history.append(snapshot)
        if len(self.history) > self.max_history_len:
            self.history.pop(0)

    def get_population_series(self) -> List[int]:
        return [s.total_population for s in self.history]

    def get_herbivore_series(self) -> List[int]:
        return [s.herbivore_count for s in self.history]

    def get_carnivore_series(self) -> List[int]:
        return [s.carnivore_count for s in self.history]

    def get_vegetation_series(self) -> List[float]:
        return [s.total_vegetation for s in self.history]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_interval": self.record_interval,
            "max_history_len": self.max_history_len,
            "total_births": self.total_births,
            "total_deaths": self.total_deaths,
            "history": [
                {
                    "tick": s.tick,
                    "pop": s.total_population,
                    "herb": s.herbivore_count,
                    "omni": s.omnivore_count,
                    "carn": s.carnivore_count,
                    "biomass": s.total_biomass,
                    "veg": s.total_vegetation,
                    "extinct": s.extinct_species_count,
                    "active_sp": s.active_species_count,
                    "avg_speed": s.average_speed,
                    "avg_size": s.average_size,
                }
                for s in self.history
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatsTracker":
        st = cls(
            record_interval=data.get("record_interval", 15),
            max_history_len=data.get("max_history_len", 400),
        )
        st.total_births = data.get("total_births", 0)
        st.total_deaths = data.get("total_deaths", 0)
        for h in data.get("history", []):
            snapshot = EcosystemSnapshot(
                tick=h["tick"],
                total_population=h["pop"],
                herbivore_count=h["herb"],
                omnivore_count=h["omni"],
                carnivore_count=h["carn"],
                total_biomass=h["biomass"],
                total_vegetation=h["veg"],
                extinct_species_count=h["extinct"],
                active_species_count=h["active_sp"],
                average_speed=h["avg_speed"],
                average_size=h["avg_size"],
            )
            st.history.append(snapshot)
        return st
