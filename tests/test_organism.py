"""Unit tests for organism autonomy, metabolism, hunting, and life cycle."""
import pytest
import random
from ecosystem.entities.genome import Genome
from ecosystem.entities.organism import Organism, OrganismAction
from ecosystem.world.grid import WorldGrid
from ecosystem.world.weather import WeatherSystem

def test_organism_initial_state():
    g = Genome(size=1.0)
    org = Organism(organism_id=1, species_id=1, genome=g, x=10.0, y=10.0)
    assert org.is_alive
    assert org.health == 80.0
    assert org.energy == 75.0
    assert org.water == 60.0
    assert org.age_ticks == 0

def test_organism_metabolism_and_starvation():
    g = Genome(size=1.0, metabolism=1.5)
    org = Organism(organism_id=1, species_id=1, genome=g, x=10.0, y=10.0)
    world = WorldGrid(width=30, height=30, seed=42)
    weather = WeatherSystem(seed=42)
    rng = random.Random(42)

    initial_energy = org.energy
    # Step without food
    for _ in range(50):
        org.step(world, weather, [], rng)

    assert org.energy < initial_energy

def test_herbivore_grazing():
    g = Genome(size=1.0, diet=0.0)
    org = Organism(organism_id=1, species_id=1, genome=g, x=5.0, y=5.0)
    org.energy = 20.0  # Make hungry
    world = WorldGrid(width=20, height=20, seed=42)
    world.vegetation[5, 5] = 80.0
    weather = WeatherSystem(seed=42)
    rng = random.Random(42)

    # Step to forage
    org.step(world, weather, [], rng)
    assert org.energy > 20.0
    assert org.food_eaten > 0.0

def test_carnivore_predation():
    carn_g = Genome(size=1.8, diet=1.0, speed=2.0, aggression=0.9)
    prey_g = Genome(size=0.6, diet=0.0, speed=0.5)

    carn = Organism(organism_id=1, species_id=1, genome=carn_g, x=10.0, y=10.0)
    prey = Organism(organism_id=2, species_id=2, genome=prey_g, x=10.5, y=10.5)
    carn.energy = 25.0  # Starving predator

    world = WorldGrid(width=30, height=30, seed=42)
    weather = WeatherSystem(seed=42)
    rng = random.Random(42)

    # Execute hunting step
    carn.step(world, weather, [prey], rng)
    # Predator should have attacked prey
    assert prey.health < prey.max_health or not prey.is_alive
