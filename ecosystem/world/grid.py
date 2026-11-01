"""Grid world implementation with procedural map generation, resources, and terrain dynamics."""
import random
import math
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from ecosystem.world.biome import BiomeType, BIOME_REGISTRY, determine_biome
from ecosystem.world.weather import WeatherSystem

class WorldGrid:
    """Represents the 2D environmental simulation surface."""

    def __init__(self, width: int = 120, height: int = 80, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.rng = random.Random(self.seed)

        # 2D Layers (float / int arrays)
        self.elevation = np.zeros((height, width), dtype=np.float32)
        self.moisture = np.zeros((height, width), dtype=np.float32)
        self.biome_map = np.zeros((height, width), dtype=np.int32)
        self.vegetation = np.zeros((height, width), dtype=np.float32)
        self.max_vegetation = np.zeros((height, width), dtype=np.float32)
        self.fertility = np.zeros((height, width), dtype=np.float32)
        self.carrion = np.zeros((height, width), dtype=np.float32)  # Decaying meat/detritus

        # Generate world
        self._generate_terrain()

    def _generate_noise_map(self, octaves: int = 4, scale: float = 25.0) -> np.ndarray:
        """Procedural noise map using value-noise with bicubic/smooth interpolation."""
        rng = np.random.default_rng(self.rng.randint(0, 1000000))
        noise = np.zeros((self.height, self.width), dtype=np.float32)

        weight = 1.0
        total_weight = 0.0

        for oct in range(octaves):
            step = max(2, int(scale / (2 ** oct)))
            grid_h = int(math.ceil(self.height / step)) + 2
            grid_w = int(math.ceil(self.width / step)) + 2
            grid = rng.uniform(0.0, 1.0, (grid_h, grid_w)).astype(np.float32)

            # Bilinear interpolation
            y_indices = np.arange(self.height, dtype=np.float32) / step
            x_indices = np.arange(self.width, dtype=np.float32) / step

            y0 = np.floor(y_indices).astype(np.int32)
            x0 = np.floor(x_indices).astype(np.int32)
            y1 = y0 + 1
            x1 = x0 + 1

            fy = (y_indices - y0)[:, np.newaxis]
            fx = (x_indices - x0)[np.newaxis, :]

            # Smoothstep curve for natural transitions: 3*x^2 - 2*x^3
            fy = fy * fy * (3.0 - 2.0 * fy)
            fx = fx * fx * (3.0 - 2.0 * fx)

            top = grid[y0[:, None], x0] * (1.0 - fx) + grid[y0[:, None], x1] * fx
            bottom = grid[y1[:, None], x0] * (1.0 - fx) + grid[y1[:, None], x1] * fx
            interpolated = top * (1.0 - fy) + bottom * fy

            noise += interpolated * weight
            total_weight += weight
            weight *= 0.5

        noise /= total_weight
        # Normalize to [0, 1]
        noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
        return noise

    def _generate_terrain(self) -> None:
        """Create diverse natural topography and water basins."""
        # Elevation map
        raw_elev = self._generate_noise_map(octaves=4, scale=35.0)
        # Island gradient to create surrounded natural landmass with ocean shores
        y, x = np.ogrid[:self.height, :self.width]
        center_y, center_x = self.height / 2.0, self.width / 2.0
        dist_from_center = np.sqrt(((x - center_x) / center_x) ** 2 + ((y - center_y) / center_y) ** 2)
        island_falloff = 1.0 - np.clip(dist_from_center * 0.75, 0.0, 0.95)
        self.elevation = np.clip(raw_elev * 0.75 + island_falloff * 0.25, 0.0, 1.0)

        # Moisture map (slightly shifted scale for climate variation)
        self.moisture = self._generate_noise_map(octaves=3, scale=40.0)

        # Populate biomes and resource maximums
        biome_list = list(BiomeType)
        for r in range(self.height):
            for c in range(self.width):
                b_type = determine_biome(float(self.elevation[r, c]), float(self.moisture[r, c]))
                b_props = BIOME_REGISTRY[b_type]
                self.biome_map[r, c] = biome_list.index(b_type)
                self.fertility[r, c] = b_props.fertility
                self.max_vegetation[r, c] = b_props.max_vegetation
                # Initial vegetation is a random fraction of max capacity
                self.vegetation[r, c] = b_props.max_vegetation * self.rng.uniform(0.3, 0.8)

    def get_biome_at(self, x: int, y: int) -> BiomeType:
        """Get biome at integer coordinate with boundary wrapping/clamping."""
        cx = max(0, min(self.width - 1, int(x)))
        cy = max(0, min(self.height - 1, int(y)))
        b_idx = self.biome_map[cy, cx]
        return list(BiomeType)[b_idx]

    def is_water(self, x: int, y: int) -> bool:
        """Checks if tile is drinkable freshwater or ocean water."""
        b = self.get_biome_at(x, y)
        return BIOME_REGISTRY[b].is_water_source

    def is_walkable(self, x: float, y: float) -> bool:
        """Checks if tile is navigable by land organisms."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        b = self.get_biome_at(int(x), int(y))
        return BIOME_REGISTRY[b].walkable

    def get_movement_cost(self, x: float, y: float) -> float:
        """Energy multiplier for tile terrain."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 2.5
        b = self.get_biome_at(int(x), int(y))
        return BIOME_REGISTRY[b].movement_cost

    def get_temperature_at(self, x: float, y: float, weather: WeatherSystem) -> float:
        """Computes current Celsius temperature considering biome, elevation, weather and time."""
        b = self.get_biome_at(int(x), int(y))
        base_temp = BIOME_REGISTRY[b].ambient_temp
        # Higher elevation = colder (-15 deg per 1.0 elevation)
        elev_cost = (self.elevation[int(y), int(x)] - 0.3) * 15.0
        # Time of day cooling at night (-4 at midnight, +4 at noon)
        daylight_temp = (weather.daylight_intensity - 0.5) * 8.0
        return base_temp - elev_cost + weather.current_state.temperature_offset + weather.seasonal_temp_offset + daylight_temp

    def update_resources(self, weather: WeatherSystem) -> None:
        """Regenerate plant food and decay carrion over time."""
        # Plant growth depends on fertility, moisture delta, and sunlight
        sunlight = max(0.2, weather.daylight_intensity)
        growth_rate = 0.08 * self.fertility * weather.current_state.moisture_delta * sunlight

        # Logistic vegetation growth: dV/dt = r * V * (1 - V / K) + base_sprout
        free_capacity = np.maximum(0.0, self.max_vegetation - self.vegetation)
        growth = growth_rate * np.sqrt(self.vegetation + 1.0) * (free_capacity / (self.max_vegetation + 1e-4))
        self.vegetation = np.clip(self.vegetation + growth, 0.0, self.max_vegetation)

        # Slowly decompose carrion
        self.carrion = np.maximum(0.0, self.carrion * 0.995 - 0.02)

    def consume_vegetation(self, x: int, y: int, amount: float) -> float:
        """Graze plant food at (x, y). Returns amount actually consumed."""
        if 0 <= x < self.width and 0 <= y < self.height:
            available = self.vegetation[y, x]
            consumed = min(available, amount)
            self.vegetation[y, x] -= consumed
            return consumed
        return 0.0

    def consume_carrion(self, x: int, y: int, amount: float) -> float:
        """Eat detritus/carrion at (x, y). Returns amount eaten."""
        if 0 <= x < self.width and 0 <= y < self.height:
            available = self.carrion[y, x]
            consumed = min(available, amount)
            self.carrion[y, x] -= consumed
            return consumed
        return 0.0

    def add_carrion(self, x: int, y: int, amount: float) -> None:
        """Deposit carrion at location (e.g. deceased organism)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.carrion[y, x] = min(150.0, self.carrion[y, x] + amount)

    def find_nearest_water(self, start_x: float, start_y: float, search_radius: int = 15) -> Optional[Tuple[int, int]]:
        """Fast radial search for the nearest water tile."""
        ix, iy = int(start_x), int(start_y)
        # Check starting tile first
        if self.is_water(ix, iy):
            return (ix, iy)

        for r in range(1, search_radius + 1):
            # Scan perimeter of square at radius r
            for dx in range(-r, r + 1):
                for dy in (-r, r):
                    tx, ty = ix + dx, iy + dy
                    if 0 <= tx < self.width and 0 <= ty < self.height and self.is_water(tx, ty):
                        return (tx, ty)
            for dy in range(-r + 1, r):
                for dx in (-r, r):
                    tx, ty = ix + dx, iy + dy
                    if 0 <= tx < self.width and 0 <= ty < self.height and self.is_water(tx, ty):
                        return (tx, ty)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize world grid state for persistence."""
        return {
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
            "elevation": self.elevation.tolist(),
            "moisture": self.moisture.tolist(),
            "biome_map": self.biome_map.tolist(),
            "vegetation": self.vegetation.tolist(),
            "max_vegetation": self.max_vegetation.tolist(),
            "fertility": self.fertility.tolist(),
            "carrion": self.carrion.tolist(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldGrid":
        """Deserialize world grid state."""
        world = cls(width=data["width"], height=data["height"], seed=data["seed"])
        world.elevation = np.array(data["elevation"], dtype=np.float32)
        world.moisture = np.array(data["moisture"], dtype=np.float32)
        world.biome_map = np.array(data["biome_map"], dtype=np.int32)
        world.vegetation = np.array(data["vegetation"], dtype=np.float32)
        world.max_vegetation = np.array(data["max_vegetation"], dtype=np.float32)
        world.fertility = np.array(data["fertility"], dtype=np.float32)
        world.carrion = np.array(data["carrion"], dtype=np.float32)
        return world
