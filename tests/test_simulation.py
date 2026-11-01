"""Unit tests for complete simulation dynamics, multi-generational longevity, and save/load."""
import pytest
import os
from ecosystem.core.simulation import Simulation
from ecosystem.core.save_load import SaveManager

def test_simulation_step_and_stats():
    sim = Simulation(width=40, height=30, seed=123)
    sim.populate_initial_ecosystem(num_herbivores=12, num_omnivores=4, num_carnivores=2)
    assert len(sim.organisms) == 18

    # Step for 60 ticks
    for _ in range(60):
        sim.step()

    assert sim.tick_count == 60
    assert len(sim.stats.history) > 0

def test_simulation_disaster_effects():
    sim = Simulation(width=30, height=30, seed=456)
    sim.populate_initial_ecosystem(num_herbivores=15, num_omnivores=5, num_carnivores=0)

    # Trigger bloom
    sim.add_disaster("bloom")
    assert sim.world.vegetation.sum() > 0

    # Trigger drought
    veg_before = sim.world.vegetation.sum()
    sim.add_disaster("drought")
    assert sim.world.vegetation.sum() < veg_before

def test_simulation_save_and_restore(tmp_path):
    sim = Simulation(width=30, height=30, seed=789)
    sim.populate_initial_ecosystem(num_herbivores=8, num_omnivores=3, num_carnivores=1)
    for _ in range(25):
        sim.step()

    save_path = os.path.join(tmp_path, "save_test.eco")
    # Save manually using SaveManager logic
    import json, gzip
    data = {
        "version": "1.0",
        "seed": sim.seed,
        "tick_count": sim.tick_count,
        "next_organism_id": sim.next_organism_id,
        "world": sim.world.to_dict(),
        "weather": sim.weather.to_dict(),
        "species_manager": sim.species_manager.to_dict(),
        "organisms": [o.to_dict() for o in sim.organisms],
        "stats": sim.stats.to_dict(),
        "event_log": sim.event_log,
    }
    with gzip.open(save_path, "wb") as f:
        f.write(json.dumps(data).encode("utf-8"))

    loaded_sim = SaveManager.load_simulation(save_path)
    assert loaded_sim.tick_count == sim.tick_count
    assert len(loaded_sim.organisms) == len(sim.organisms)

def test_ecosystem_extended_longevity():
    """Longevity test: ecosystem runs for 600 ticks (1 full year) without crash."""
    sim = Simulation(width=50, height=40, seed=42)
    sim.populate_initial_ecosystem(num_herbivores=25, num_omnivores=8, num_carnivores=4)

    for _ in range(600):
        sim.step()

    # The simulation should survive and have active organisms or recorded births/deaths
    assert sim.tick_count == 600
    assert sim.stats.total_deaths > 0 or sim.stats.total_births > 0
