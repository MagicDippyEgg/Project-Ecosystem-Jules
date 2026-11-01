"""Weather and environmental conditions simulation."""
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class WeatherCondition(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    DROUGHT = "drought"
    HEATWAVE = "heatwave"
    COLDSNAP = "coldsnap"

@dataclass
class WeatherState:
    condition: WeatherCondition
    temperature_offset: float    # Celsius added or subtracted from ambient
    moisture_delta: float        # Multiplier on tile moisture / plant growth
    visibility_factor: float     # Multiplier on organism sight radius (0.4 - 1.0)
    stamina_drain_factor: float  # Multiplier on organism movement energy cost
    duration_remaining: int      # Ticks remaining for this weather

WEATHER_PROFILES = {
    WeatherCondition.CLEAR: {
        "temp_offset": 0.0,
        "moisture_delta": 1.0,
        "visibility": 1.0,
        "stamina_drain": 1.0,
        "min_duration": 300,
        "max_duration": 900,
    },
    WeatherCondition.CLOUDY: {
        "temp_offset": -2.0,
        "moisture_delta": 1.1,
        "visibility": 0.9,
        "stamina_drain": 1.0,
        "min_duration": 200,
        "max_duration": 600,
    },
    WeatherCondition.RAIN: {
        "temp_offset": -4.0,
        "moisture_delta": 1.8,
        "visibility": 0.75,
        "stamina_drain": 1.15,
        "min_duration": 250,
        "max_duration": 600,
    },
    WeatherCondition.STORM: {
        "temp_offset": -6.0,
        "moisture_delta": 2.5,
        "visibility": 0.5,
        "stamina_drain": 1.4,
        "min_duration": 150,
        "max_duration": 400,
    },
    WeatherCondition.DROUGHT: {
        "temp_offset": 6.0,
        "moisture_delta": 0.2,
        "visibility": 1.0,
        "stamina_drain": 1.3,
        "min_duration": 400,
        "max_duration": 900,
    },
    WeatherCondition.HEATWAVE: {
        "temp_offset": 10.0,
        "moisture_delta": 0.5,
        "visibility": 0.9,
        "stamina_drain": 1.5,
        "min_duration": 300,
        "max_duration": 700,
    },
    WeatherCondition.COLDSNAP: {
        "temp_offset": -12.0,
        "moisture_delta": 0.8,
        "visibility": 0.85,
        "stamina_drain": 1.35,
        "min_duration": 300,
        "max_duration": 700,
    },
}

class WeatherSystem:
    """Manages weather transitions, day/night cycle, and seasonal trends."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.tick = 0
        self.ticks_per_day = 600       # 600 ticks = 1 in-simulation day
        self.days_per_year = 12        # 12 days = 1 annual cycle (seasons)
        self.current_state = self._generate_weather(WeatherCondition.CLEAR)

    def _generate_weather(self, condition: WeatherCondition) -> WeatherState:
        profile = WEATHER_PROFILES[condition]
        duration = self.rng.randint(profile["min_duration"], profile["max_duration"])
        return WeatherState(
            condition=condition,
            temperature_offset=profile["temp_offset"],
            moisture_delta=profile["moisture_delta"],
            visibility_factor=profile["visibility"],
            stamina_drain_factor=profile["stamina_drain"],
            duration_remaining=duration,
        )

    def transition_weather(self, force_condition: WeatherCondition | None = None) -> None:
        """Trigger a weather transition either randomly or forced."""
        if force_condition is not None:
            self.current_state = self._generate_weather(force_condition)
            return

        # Weather transition probabilities based on current condition
        transitions = {
            WeatherCondition.CLEAR: [
                (WeatherCondition.CLEAR, 0.45),
                (WeatherCondition.CLOUDY, 0.35),
                (WeatherCondition.HEATWAVE, 0.1),
                (WeatherCondition.DROUGHT, 0.1),
            ],
            WeatherCondition.CLOUDY: [
                (WeatherCondition.CLEAR, 0.35),
                (WeatherCondition.RAIN, 0.40),
                (WeatherCondition.COLDSNAP, 0.15),
                (WeatherCondition.STORM, 0.10),
            ],
            WeatherCondition.RAIN: [
                (WeatherCondition.CLOUDY, 0.5),
                (WeatherCondition.STORM, 0.25),
                (WeatherCondition.CLEAR, 0.25),
            ],
            WeatherCondition.STORM: [
                (WeatherCondition.RAIN, 0.6),
                (WeatherCondition.CLOUDY, 0.4),
            ],
            WeatherCondition.DROUGHT: [
                (WeatherCondition.HEATWAVE, 0.4),
                (WeatherCondition.CLEAR, 0.5),
                (WeatherCondition.RAIN, 0.1),
            ],
            WeatherCondition.HEATWAVE: [
                (WeatherCondition.CLEAR, 0.5),
                (WeatherCondition.DROUGHT, 0.3),
                (WeatherCondition.STORM, 0.2),
            ],
            WeatherCondition.COLDSNAP: [
                (WeatherCondition.CLEAR, 0.5),
                (WeatherCondition.CLOUDY, 0.4),
                (WeatherCondition.STORM, 0.1),
            ],
        }

        weights_pair = transitions.get(self.current_state.condition, [(WeatherCondition.CLEAR, 1.0)])
        choices, weights = zip(*weights_pair)
        next_cond = self.rng.choices(choices, weights=weights)[0]
        self.current_state = self._generate_weather(next_cond)

    def step(self) -> None:
        """Advance time by one tick and update weather duration."""
        self.tick += 1
        self.current_state.duration_remaining -= 1
        if self.current_state.duration_remaining <= 0:
            self.transition_weather()

    @property
    def day(self) -> int:
        return self.tick // self.ticks_per_day

    @property
    def time_of_day(self) -> float:
        """Normalized time of day [0.0, 1.0). 0.0=dawn, 0.25=noon, 0.5=dusk, 0.75=midnight."""
        return (self.tick % self.ticks_per_day) / self.ticks_per_day

    @property
    def daylight_intensity(self) -> float:
        """Light level [0.15 to 1.0]. Peak daylight at 0.25, lowest at 0.75."""
        import math
        # Cosine curve with peak 1.0 at 0.25 and min 0.15 at 0.75
        phase = (self.time_of_day - 0.25) * 2.0 * math.pi
        raw = 0.5 + 0.5 * math.cos(phase)
        return max(0.15, raw)

    @property
    def is_night(self) -> bool:
        return self.daylight_intensity < 0.35

    @property
    def seasonal_temp_offset(self) -> float:
        """Seasonal Celsius variation throughout the year."""
        import math
        year_progress = (self.day % self.days_per_year) / self.days_per_year
        # Summer peak, winter trough (-8.0 to +8.0)
        return 8.0 * math.sin(year_progress * 2.0 * math.pi)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "condition": self.current_state.condition.value,
            "temp_offset": self.current_state.temperature_offset,
            "moisture_delta": self.current_state.moisture_delta,
            "visibility_factor": self.current_state.visibility_factor,
            "stamina_drain_factor": self.current_state.stamina_drain_factor,
            "duration_remaining": self.current_state.duration_remaining,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], seed: int = 42) -> "WeatherSystem":
        ws = cls(seed=seed)
        ws.tick = data.get("tick", 0)
        ws.current_state = WeatherState(
            condition=WeatherCondition(data.get("condition", "clear")),
            temperature_offset=data.get("temp_offset", 0.0),
            moisture_delta=data.get("moisture_delta", 1.0),
            visibility_factor=data.get("visibility_factor", 1.0),
            stamina_drain_factor=data.get("stamina_drain_factor", 1.0),
            duration_remaining=data.get("duration_remaining", 300),
        )
        return ws
