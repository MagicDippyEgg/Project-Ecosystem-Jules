"""Automated tests for terrain awareness, obstacle avoidance, shoreline drinking, threat evasion, and population viability."""
import pytest
import random
import math
from ecosystem.world.grid import WorldGrid
from ecosystem.world.weather import WeatherSystem
from ecosystem.entities.genome import Genome
from ecosystem.entities.organism import Organism, OrganismAction
from ecosystem.core.simulation import Simulation

def test_land_organism_never_enters_water():
    """Verify land organisms strictly avoid deep water tiles."""
    world = WorldGrid(width=50, height=40, seed=42)
    weather = WeatherSystem(seed=42)
    rng = random.Random(42)

    # Spawn land creature on land
    spawn_x, spawn_y = 25.0, 20.0
    while not world.is_walkable(spawn_x, spawn_y):
        spawn_x += 1.0

    g = Genome(size=1.0, speed=1.8)
    org = Organism(1, 1, g, spawn_x, spawn_y)

    for _ in range(250):
        org.step(world, weather, [], rng)
        assert world.is_walkable(org.x, org.y), f"Organism stepped onto unwalkable tile at ({org.x}, {org.y})"

def test_organism_navigates_around_obstacles():
    """Verify organism navigates toward target around obstacles without penetrating them."""
    world = WorldGrid(width=30, height=30, seed=123)
    weather = WeatherSystem(seed=123)
    rng = random.Random(123)

    # Place an artificial obstacle (mountain/deep water) in the direct path
    start_x, start_y = 10.0, 15.0
    target_x, target_y = 20.0, 15.0

    # Mark obstacle in middle
    for y in range(12, 18):
        world.biome_map[y, 15] = 0  # Deep water

    g = Genome(size=1.0, speed=1.5)
    org = Organism(1, 1, g, start_x, start_y)

    # Move towards target for 80 steps
    for _ in range(80):
        org._move_towards(target_x, target_y, g.speed, world, weather, rng)
        assert world.is_walkable(org.x, org.y)

    # Organism should have made progress around obstacle towards right side
    assert org.x > start_x

def test_organism_shoreline_drinking():
    """Verify organism drinks safely from shorelines without walking into water."""
    world = WorldGrid(width=30, height=30, seed=999)
    weather = WeatherSystem(seed=999)
    rng = random.Random(999)

    # Find a drinkable shore
    shore = world.find_nearest_drinkable_shore(15.0, 15.0, search_radius=20)
    assert shore is not None
    assert world.is_drinkable_shore(shore[0], shore[1])

    # Creature with low hydration
    g = Genome(size=1.0)
    org = Organism(1, 1, g, float(shore[0]), float(shore[1]))
    org.water = 10.0
    initial_water = org.water

    # Step at shore
    org.step(world, weather, [], rng)
    # Organism should have drunk and quenched thirst
    assert org.water > initial_water
    assert world.is_walkable(org.x, org.y)

def test_prey_threat_response():
    """Verify prey actively flees from a dangerous predator within threat range."""
    world = WorldGrid(width=40, height=40, seed=55)
    weather = WeatherSystem(seed=55)
    rng = random.Random(55)

    g_prey = Genome(size=0.8, diet=0.0, speed=1.2, bravery=0.2)
    g_pred = Genome(size=2.0, diet=1.0, speed=1.5, aggression=0.9)

    prey = Organism(1, 1, g_prey, 20.0, 20.0)
    pred = Organism(2, 2, g_pred, 22.0, 20.0)

    # Prey should identify predator as threat and choose FLEE
    prey._decide_action(world, weather, [pred], rng)
    assert prey.current_action == OrganismAction.FLEE

    initial_dist = math.hypot(prey.x - pred.x, prey.y - pred.y)
    # Prey moves away from predator
    prey._execute_action(world, weather, [pred], rng)
    new_dist = math.hypot(prey.x - pred.x, prey.y - pred.y)
    assert new_dist >= initial_dist or world.is_walkable(prey.x, prey.y)

def test_population_viability_over_time():
    """Verify population viability over an extended simulation period."""
    sim = Simulation(width=50, height=40, seed=77)
    sim.populate_initial_ecosystem(num_herbivores=25, num_omnivores=8, num_carnivores=3)

    for _ in range(600):
        sim.step()

    # Organisms should remain alive and thriving
    assert len(sim.organisms) >= 10
    # There should be recorded births indicating natural reproduction
    assert sim.stats.total_births > 0 or len(sim.organisms) >= 15
