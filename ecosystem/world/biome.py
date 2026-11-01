"""Biome definitions and properties for the ecosystem."""
from enum import Enum
from dataclasses import dataclass
from typing import Tuple

class BiomeType(Enum):
    DEEP_WATER = "deep_water"
    SHALLOW_WATER = "shallow_water"
    BEACH = "beach"
    PLAINS = "plains"
    FOREST = "forest"
    RAINFOREST = "rainforest"
    DESERT = "desert"
    SAVANNA = "savanna"
    TUNDRA = "tundra"
    MOUNTAIN = "mountain"

@dataclass(frozen=True)
class BiomeProperties:
    name: str
    biome_type: BiomeType
    color: Tuple[int, int, int]
    walkable: bool
    swimmable: bool
    fertility: float          # Base rate of plant/food growth (0.0 to 2.0)
    max_vegetation: float     # Maximum vegetation capacity per tile
    movement_cost: float      # Energy multiplier for traversing (1.0 = normal)
    ambient_temp: float       # Base Celsius temperature (e.g. 20.0)
    is_water_source: bool     # Can creatures drink directly here?

BIOME_REGISTRY = {
    BiomeType.DEEP_WATER: BiomeProperties(
        name="Deep Water",
        biome_type=BiomeType.DEEP_WATER,
        color=(24, 64, 140),
        walkable=False,
        swimmable=True,
        fertility=0.1,
        max_vegetation=15.0,
        movement_cost=2.2,
        ambient_temp=14.0,
        is_water_source=True,
    ),
    BiomeType.SHALLOW_WATER: BiomeProperties(
        name="Shallow Water",
        biome_type=BiomeType.SHALLOW_WATER,
        color=(46, 120, 190),
        walkable=True,
        swimmable=True,
        fertility=0.4,
        max_vegetation=30.0,
        movement_cost=1.6,
        ambient_temp=17.0,
        is_water_source=True,
    ),
    BiomeType.BEACH: BiomeProperties(
        name="Beach",
        biome_type=BiomeType.BEACH,
        color=(225, 210, 150),
        walkable=True,
        swimmable=False,
        fertility=0.2,
        max_vegetation=20.0,
        movement_cost=1.2,
        ambient_temp=22.0,
        is_water_source=False,
    ),
    BiomeType.PLAINS: BiomeProperties(
        name="Plains",
        biome_type=BiomeType.PLAINS,
        color=(115, 185, 75),
        walkable=True,
        swimmable=False,
        fertility=1.0,
        max_vegetation=100.0,
        movement_cost=1.0,
        ambient_temp=20.0,
        is_water_source=False,
    ),
    BiomeType.FOREST: BiomeProperties(
        name="Forest",
        biome_type=BiomeType.FOREST,
        color=(38, 125, 52),
        walkable=True,
        swimmable=False,
        fertility=1.5,
        max_vegetation=160.0,
        movement_cost=1.2,
        ambient_temp=18.0,
        is_water_source=False,
    ),
    BiomeType.RAINFOREST: BiomeProperties(
        name="Rainforest",
        biome_type=BiomeType.RAINFOREST,
        color=(20, 95, 45),
        walkable=True,
        swimmable=False,
        fertility=2.0,
        max_vegetation=220.0,
        movement_cost=1.4,
        ambient_temp=26.0,
        is_water_source=False,
    ),
    BiomeType.SAVANNA: BiomeProperties(
        name="Savanna",
        biome_type=BiomeType.SAVANNA,
        color=(190, 175, 75),
        walkable=True,
        swimmable=False,
        fertility=0.6,
        max_vegetation=70.0,
        movement_cost=1.0,
        ambient_temp=27.0,
        is_water_source=False,
    ),
    BiomeType.DESERT: BiomeProperties(
        name="Desert",
        biome_type=BiomeType.DESERT,
        color=(220, 180, 95),
        walkable=True,
        swimmable=False,
        fertility=0.08,
        max_vegetation=15.0,
        movement_cost=1.3,
        ambient_temp=35.0,
        is_water_source=False,
    ),
    BiomeType.TUNDRA: BiomeProperties(
        name="Tundra",
        biome_type=BiomeType.TUNDRA,
        color=(175, 200, 205),
        walkable=True,
        swimmable=False,
        fertility=0.25,
        max_vegetation=40.0,
        movement_cost=1.3,
        ambient_temp=-2.0,
        is_water_source=False,
    ),
    BiomeType.MOUNTAIN: BiomeProperties(
        name="Mountain",
        biome_type=BiomeType.MOUNTAIN,
        color=(135, 130, 130),
        walkable=True,
        swimmable=False,
        fertility=0.15,
        max_vegetation=25.0,
        movement_cost=1.8,
        ambient_temp=5.0,
        is_water_source=False,
    ),
}

def determine_biome(elevation: float, moisture: float) -> BiomeType:
    """Determine biome type given normalized elevation [0, 1] and moisture [0, 1]."""
    if elevation < 0.22:
        return BiomeType.DEEP_WATER
    elif elevation < 0.32:
        return BiomeType.SHALLOW_WATER
    elif elevation < 0.36:
        return BiomeType.BEACH
    elif elevation > 0.82:
        return BiomeType.MOUNTAIN
    elif elevation > 0.70:
        return BiomeType.TUNDRA if moisture < 0.55 else BiomeType.MOUNTAIN
    else:
        # Mid-level land
        if moisture < 0.22:
            return BiomeType.DESERT
        elif moisture < 0.42:
            return BiomeType.SAVANNA
        elif moisture < 0.72:
            return BiomeType.PLAINS
        elif moisture < 0.88:
            return BiomeType.FOREST
        else:
            return BiomeType.RAINFOREST
