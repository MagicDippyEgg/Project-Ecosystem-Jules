"""Unit tests for genetics, traits, crossover, and speciation taxonomy."""
import pytest
import random
from ecosystem.entities.genome import Genome
from ecosystem.entities.species import SpeciesManager

def test_genome_initialization():
    g = Genome(size=1.2, speed=1.4, diet=0.2)
    assert g.size == 1.2
    assert g.speed == 1.4
    assert len(g.color) == 3
    assert all(0 <= c <= 255 for c in g.color)

def test_genome_mutation():
    rng = random.Random(42)
    g1 = Genome(size=1.0, speed=1.0, mutation_rate=0.5)
    g2 = g1.mutate(rng)
    # Genome should have mutated
    assert g2.lineage_tag != g1.lineage_tag
    assert 0.4 <= g2.size <= 2.8
    assert 0.3 <= g2.speed <= 2.5

def test_genome_crossover():
    rng = random.Random(123)
    p1 = Genome(size=0.8, speed=2.0, diet=0.1)
    p2 = Genome(size=2.0, speed=0.5, diet=0.9)
    child = Genome.crossover(p1, p2, rng)
    assert child is not None
    assert 0.4 <= child.size <= 2.8

def test_species_classification_and_branching():
    sm = SpeciesManager()
    g_herb1 = Genome(size=0.8, speed=1.2, diet=0.1)
    sp1 = sm.classify_or_speciate(g_herb1, current_tick=0)
    assert sp1.species_id == 1

    # Close relative should match same species
    g_herb_close = Genome(size=0.82, speed=1.18, diet=0.12)
    sp_same = sm.classify_or_speciate(g_herb_close, current_tick=10)
    assert sp_same.species_id == sp1.species_id

    # Divergent carnivore should branch into new species
    g_carn = Genome(size=2.2, speed=1.6, diet=0.95, aggression=0.8)
    sp2 = sm.classify_or_speciate(g_carn, current_tick=50)
    assert sp2.species_id != sp1.species_id
    assert sp2.species_id == 2
