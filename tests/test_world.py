"""Unit tests for world generation, biomes, and weather dynamics."""
import pytest
import numpy as np
from ecosystem.world.biome import BiomeType, BIOME_REGISTRY, determine_biome
from ecosystem.world.weather import WeatherSystem, WeatherCondition
from ecosystem.world.grid import WorldGrid

def test_biome_determination():
    # Ocean elevation
    assert determine_biome(0.1, 0.5) == BiomeType.DEEP_WATER
    assert determine_biome(0.25, 0.5) == BiomeType.SHALLOW_WATER
    assert determine_biome(0.34, 0.5) == BiomeType.BEACH
    # High elevation
    assert determine_biome(0.85, 0.5) == BiomeType.MOUNTAIN
    # Mid-elevation dry vs wet
    assert determine_biome(0.5, 0.1) == BiomeType.DESERT
    assert determine_biome(0.5, 0.95) == BiomeType.RAINFOREST

def test_weather_system_progression():
    ws = WeatherSystem(seed=42)
    assert ws.tick == 0
    assert ws.day == 0
    assert 0.15 <= ws.daylight_intensity <= 1.0

    # Advance 600 ticks (1 day)
    for _ in range(600):
        ws.step()
    assert ws.day == 1

def test_weather_transitions():
    ws = WeatherSystem(seed=123)
    ws.transition_weather(WeatherCondition.STORM)
    assert ws.current_state.condition == WeatherCondition.STORM
    assert ws.current_state.visibility_factor < 1.0
    assert ws.current_state.stamina_drain_factor > 1.0

def test_world_grid_generation():
    grid = WorldGrid(width=50, height=40, seed=777)
    assert grid.elevation.shape == (40, 50)
    assert grid.moisture.shape == (40, 50)
    assert grid.vegetation.shape == (40, 50)
    assert np.all(grid.elevation >= 0.0) and np.all(grid.elevation <= 1.0)
    assert np.all(grid.vegetation >= 0.0)

def test_world_resource_consumption():
    grid = WorldGrid(width=30, height=30, seed=42)
    # Set known vegetation
    grid.vegetation[10, 10] = 50.0
    consumed = grid.consume_vegetation(10, 10, amount=20.0)
    assert consumed == 20.0
    assert grid.vegetation[10, 10] == 30.0

    # Overconsume
    consumed_excess = grid.consume_vegetation(10, 10, amount=50.0)
    assert consumed_excess == 30.0
    assert grid.vegetation[10, 10] == 0.0

def test_carrion_addition_and_consumption():
    grid = WorldGrid(width=20, height=20, seed=42)
    grid.add_carrion(5, 5, 40.0)
    assert grid.carrion[5, 5] == 40.0
    eaten = grid.consume_carrion(5, 5, 15.0)
    assert eaten == 15.0
    assert grid.carrion[5, 5] == 25.0
