"""
EVOLUTIONARY PROTOCOL GENERATION
================================

A genetic algorithm system that evolves comic book protocols through:
1. Mutation of existing protocols
2. Crossover between successful protocols
3. Natural selection based on quality metrics
4. Emergence of novel, high-quality protocols

This creates a self-improving protocol ecosystem that evolves toward
optimal metaphor mappings over time.
"""

import json
import random
import hashlib
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import statistics


class EvolutionStrategy(Enum):
    """Strategies for protocol evolution"""
    MUTATION_ONLY = "mutation_only"
    CROSSOVER_ONLY = "crossover_only"
    HYBRID = "hybrid"
    LAMARCKIAN = "lamarckian"  # Acquired characteristics can be inherited
    BALDWINIAN = "baldwinian"  # Learning affects fitness but not genes


class ProtocolGene(Enum):
    """Genes that can evolve in protocols"""
    DIMENSION_DEPTH = "dimension_depth"
    METAPHOR_NOVELTY = "metaphor_novelty"
    PRACTICAL_APPLICABILITY = "practical_applicability"
    EMOTIONAL_RESONANCE = "emotional_resonance"
    NARRATIVE_COMPLEXITY = "narrative_complexity"
    CROSS_DOMAIN_BRIDGING = "cross_domain_bridging"
    INSIGHT_DENSITY = "insight_density"
    ACTIONABILITY = "actionability"


@dataclass
class ProtocolGenome:
    """Genetic representation of a protocol"""
    id: str
    genes: Dict[ProtocolGene, float]  # Gene values between 0.0 and 1.0
    generation: int
    parent_ids: List[str] = field(default_factory=list)
    mutation_history: List[str] = field(default_factory=list)
    fitness_score: float = 0.0
    expressed_traits: Dict[str, Any] = field(default_factory=dict)

    def to_hash(self) -> str:
        """Create unique hash for genome"""
        gene_string = "|".join(f"{gene.value}:{value:.4f}"
                             for gene, value in sorted(self.genes.items()))
        return hashlib.md5(gene_string.encode()).hexdigest()[:12]


@dataclass
class EvolutionaryEnvironment:
    """Environment that shapes protocol evolution"""
    selection_pressure: float  # 0.0-1.0, how selective the environment is
    mutation_rate: float  # 0.0-1.0, probability of mutation
    crossover_rate: float  # 0.0-1.0, probability of crossover
    population_size: int
    elitism_count: int  # Number of top performers preserved unchanged
    gene_importance: Dict[ProtocolGene, float]  # Weight of each gene in fitness
    environmental_challenges: List[str]  # Current challenges shaping evolution


class EvolutionaryProtocolGenerator:
    """
    Evolves protocols using genetic algorithms to create increasingly
    effective metaphor mappings.
    """

    def __init__(self, environment: Optional[EvolutionaryEnvironment] = None):
        self.environment = environment or self._create_default_environment()
        self.population: List[ProtocolGenome] = []
        self.generation = 0
        self.evolution_history: List[Dict[str, Any]] = []
        self.gene_pool_diversity: List[float] = []
        self.speciation_threshold = 0.3  # Genetic distance for speciation

        # Initialize population
        self._initialize_population()

    def _create_default_environment(self) -> EvolutionaryEnvironment:
        """Create default evolutionary environment"""
        return EvolutionaryEnvironment(
            selection_pressure=0.7,
            mutation_rate=0.15,
            crossover_rate=0.4,
            population_size=50,
            elitism_count=5,
            gene_importance={
                ProtocolGene.PRACTICAL_APPLICABILITY: 0.25,
                ProtocolGene.METAPHOR_NOVELTY: 0.20,
                ProtocolGene.EMOTIONAL_RESONANCE: 0.15,
                ProtocolGene.ACTIONABILITY: 0.15,
                ProtocolGene.INSIGHT_DENSITY: 0.10,
                ProtocolGene.CROSS_DOMAIN_BRIDGING: 0.08,
                ProtocolGene.DIMENSION_DEPTH: 0.05,
                ProtocolGene.NARRATIVE_COMPLEXITY: 0.02
            },
            environmental_challenges=[
                "Need for more actionable insights",
                "Demand for novel metaphor connections",
                "Requirement for emotional engagement",
                "Pressure for cross-domain applicability"
            ]
        )

    def _initialize_population(self):
        """Initialize population with random genomes"""
        self.population = []
        for i in range(self.environment.population_size):
            genome = ProtocolGenome(
                id=f"genome_gen{self.generation:03d}_{i:03d}",
                genes=self._generate_random_genes(),
                generation=self.generation,
                parent_ids=["initial_random"]
            )
            self.population.append(genome)

    def _generate_random_genes(self) -> Dict[ProtocolGene, float]:
        """Generate random gene values"""
        genes = {}
        for gene in ProtocolGene:
            # Slight bias toward moderate values (bell curve around 0.5)
            base = random.random()
            adjustment = (random.random() - 0.5) * 0.3
            genes[gene] = max(0.0, min(1.0, 0.5 + adjustment))
        return genes

    def evaluate_fitness(self, genome: ProtocolGenome,
                        context: Optional[Dict[str, Any]] = None) -> float:
        """
        Evaluate fitness of a genome based on gene values and environmental factors.

        Higher fitness = better protocol for current environment.
        """
        if context is None:
            context = {}

        fitness = 0.0
        total_weight = 0.0

        # Base fitness from genes
        for gene, value in genome.genes.items():
            weight = self.environment.gene_importance.get(gene, 0.1)

            # Some genes have optimal ranges (not just "higher is better")
            if gene == ProtocolGene.NARRATIVE_COMPLEXITY:
                # Optimal complexity around 0.6 (complex but not overwhelming)
                optimal = 0.6
                gene_fitness = 1.0 - abs(value - optimal)
            elif gene == ProtocolGene.DIMENSION_DEPTH:
                # Depth should be sufficient but not excessive
                optimal = 0.7
                gene_fitness = 1.0 - abs(value - optimal) * 1.5
            else:
                # For most genes, higher is better
                gene_fitness = value

            fitness += gene_fitness * weight
            total_weight += weight

        # Normalize
        if total_weight > 0:
            fitness /= total_weight

        # Environmental adaptation bonus
        env_bonus = self._calculate_environmental_adaptation(genome, context)
        fitness = fitness * 0.8 + env_bonus * 0.2

        # Diversity bonus (prevent convergence to local optimum)
        diversity_bonus = self._calculate_diversity_bonus(genome)
        fitness += diversity_bonus * 0.1

        genome.fitness_score = max(0.0, min(1.0, fitness))
        return genome.fitness_score

    def _calculate_environmental_adaptation(self, genome: ProtocolGenome,
                                          context: Dict[str, Any]) -> float:
        """Calculate how well genome adapts to current environment"""
        adaptation = 0.0

        # Check alignment with environmental challenges
        challenge_keywords = {
            "actionable": ProtocolGene.ACTIONABILITY,
            "novel": ProtocolGene.METAPHOR_NOVELTY,
            "emotional": ProtocolGene.EMOTIONAL_RESONANCE,
            "cross-domain": ProtocolGene.CROSS_DOMAIN_BRIDGING,
            "practical": ProtocolGene.PRACTICAL_APPLICABILITY
        }

        for challenge in self.environment.environmental_challenges:
            for keyword, gene in challenge_keywords.items():
                if keyword in challenge.lower():
                    adaptation += genome.genes.get(gene, 0.5) * 0.2

        return min(1.0, adaptation)

    def _calculate_diversity_bonus(self, genome: ProtocolGenome) -> float:
        """Bonus for genetic diversity (prevents premature convergence)"""
        if len(self.population) < 2:
            return 0.0

        # Calculate average genetic distance from population
        distances = []
        for other in self.population:
            if other.id != genome.id:
                distance = self._genetic_distance(genome, other)
                distances.append(distance)

        if distances:
            avg_distance = statistics.mean(distances)
            # Bonus peaks at moderate distance (0.3-0.7)
            if 0.3 <= avg_distance <= 0.7:
                return 0.2
            elif avg_distance < 0.3:
                # Too similar - encourage divergence
                return (0.3 - avg_distance) * 0.5
            else:
                # Too different - encourage some convergence
                return (1.0 - avg_distance) * 0.3

        return 0.0

    def _genetic_distance(self, genome1: ProtocolGenome, genome2: ProtocolGenome) -> float:
        """Calculate genetic distance between two genomes"""
        total_distance = 0.0
        genes_compared = 0

        for gene in ProtocolGene:
            if gene in genome1.genes and gene in genome2.genes:
                distance = abs(genome1.genes[gene] - genome2.genes[gene])
                total_distance += distance
                genes_compared += 1

        return total_distance / genes_compared if genes_compared > 0 else 1.0

    def evolve_generation(self, strategy: EvolutionStrategy = EvolutionStrategy.HYBRID,
                         context: Optional[Dict[str, Any]] = None) -> List[ProtocolGenome]:
        """
        Evolve one generation of protocols.

        Returns:
            List of genomes for the new generation
        """
        self.generation += 1

        # Evaluate fitness of current population
        for genome in self.population:
            self.evaluate_fitness(genome, context)

        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness_score, reverse=True)

        # Record evolution history
        self._record_generation_stats()

        # Create next generation
        next_generation = []

        # Elitism: preserve top performers unchanged
        for i in range(min(self.environment.elitism_count, len(self.population))):
            elite = self.population[i]
            elite_genome = ProtocolGenome(
                id=f"elite_{self.generation:03d}_{i:03d}",
                genes=elite.genes.copy(),
                generation=self.generation,
                parent_ids=[elite.id],
                mutation_history=elite.mutation_history.copy(),
                fitness_score=elite.fitness_score
            )
            next_generation.append(elite_genome)

        # Fill rest of population through evolution
        while len(next_generation) < self.environment.population_size:
            parents = self._select_parents()

            if strategy == EvolutionStrategy.MUTATION_ONLY:
                child = self._mutate(parents[0])
            elif strategy == EvolutionStrategy.CROSSOVER_ONLY:
                child = self._crossover(parents[0], parents[1])
            else:  # HYBRID or others
                if random.random() < self.environment.crossover_rate:
                    child = self._crossover(parents[0], parents[1])
                else:
                    child = self._mutate(parents[0])

                # Additional mutation for hybrid
                if random.random() < self.environment.mutation_rate:
                    child = self._apply_mutation(child)

            # Lamarckian evolution: if enabled, incorporate learned improvements
            if strategy == EvolutionStrategy.LAMARCKIAN:
                child = self._lamarckian_adaptation(child, context)

            child.id = f"genome_gen{self.generation:03d}_{len(next_generation):03d}"
            child.generation = self.generation
            next_generation.append(child)

        # Update population
        self.population = next_generation

        # Evaluate fitness of new generation
        for genome in self.population:
            self.evaluate_fitness(genome, context)

        return self.population

    def _select_parents(self) -> List[ProtocolGenome]:
        """Select parents using tournament selection"""
        tournament_size = 3
        parents = []

        for _ in range(2):  # Select two parents
            tournament = random.sample(self.population,
                                     min(tournament_size, len(self.population)))
            winner = max(tournament, key=lambda g: g.fitness_score)
            parents.append(winner)

        return parents

    def _mutate(self, parent: ProtocolGenome) -> ProtocolGenome:
        """Create mutated copy of parent genome"""
        child_genes = parent.genes.copy()

        # Determine which genes to mutate
        genes_to_mutate = random.sample(
            list(ProtocolGene),
            k=random.randint(1, len(ProtocolGene) // 2)
        )

        mutation_history = parent.mutation_history.copy()

        for gene in genes_to_mutate:
            old_value = child_genes[gene]

            # Mutation amount follows normal distribution
            mutation_amount = random.gauss(0, 0.2)
            new_value = old_value + mutation_amount

            # Clamp to valid range
            child_genes[gene] = max(0.0, min(1.0, new_value))

            mutation_history.append(
                f"{gene.value}: {old_value:.3f}→{child_genes[gene]:.3f}"
            )

        return ProtocolGenome(
            id="",  # Will be set by caller
            genes=child_genes,
            generation=0,  # Will be set by caller
            parent_ids=[parent.id],
            mutation_history=mutation_history
        )

    def _crossover(self, parent1: ProtocolGenome, parent2: ProtocolGenome) -> ProtocolGenome:
        """Create child through crossover of two parents"""
        child_genes = {}

        # Uniform crossover: each gene randomly from one parent
        for gene in ProtocolGene:
            if random.random() < 0.5:
                child_genes[gene] = parent1.genes[gene]
            else:
                child_genes[gene] = parent2.genes[gene]

        # Occasionally use arithmetic crossover (blend)
        if random.random() < 0.3:
            blend_genes = random.sample(list(ProtocolGene),
                                      k=random.randint(1, 3))
            for gene in blend_genes:
                alpha = random.random()
                child_genes[gene] = (
                    alpha * parent1.genes[gene] +
                    (1 - alpha) * parent2.genes[gene]
                )

        return ProtocolGenome(
            id="",  # Will be set by caller
            genes=child_genes,
            generation=0,  # Will be set by caller
            parent_ids=[parent1.id, parent2.id],
            mutation_history=[]
        )

    def _apply_mutation(self, genome: ProtocolGenome) -> ProtocolGenome:
        """Apply additional mutation to genome"""
        return self._mutate(genome)

    def _lamarckian_adaptation(self, genome: ProtocolGenome,
                             context: Optional[Dict[str, Any]]) -> ProtocolGenome:
        """Lamarckian evolution: incorporate learned improvements into genes"""
        if not context:
            return genome

        adapted_genes = genome.genes.copy()

        # Simulate learning from environment
        for gene in ProtocolGene:
            # Learning rate based on gene plasticity
            plasticity = random.random() * 0.3

            # Adjust toward optimal for current context
            if "need_practical" in str(context).lower():
                if gene == ProtocolGene.PRACTICAL_APPLICABILITY:
                    adapted_genes[gene] = min(1.0, adapted_genes[gene] + plasticity)

            if "need_novel" in str(context).lower():
                if gene == ProtocolGene.METAPHOR_NOVELTY:
                    adapted_genes[gene] = min(1.0, adapted_genes[gene] + plasticity)

        genome.genes = adapted_genes
        return genome

    def _record_generation_stats(self):
        """Record statistics for current generation"""
        fitness_scores = [g.fitness_score for g in self.population]

        stats = {
            "generation": self.generation,
            "timestamp": datetime.now().isoformat(),
            "population_size": len(self.population),
            "avg_fitness": statistics.mean(fitness_scores) if fitness_scores else 0,
            "max_fitness": max(fitness_scores) if fitness_scores else 0,
            "min_fitness": min(fitness_scores) if fitness_scores else 0,
            "fitness_std": statistics.stdev(fitness_scores) if len(fitness_scores) > 1 else 0,
            "top_genome_id": self.population[0].id if self.population else None,
            "top_genome_fitness": self.population[0].fitness_score if self.population else 0,
            "gene_diversity": self._calculate_gene_pool_diversity()
        }

        self.evolution_history.append(stats)
        self.gene_pool_diversity.append(stats["gene_diversity"])

    def _calculate_gene_pool_diversity(self) -> float:
        """Calculate genetic diversity of population"""
        if len(self.population) < 2:
            return 1.0

        diversity = 0.0
        comparisons = 0

        for i in range(len(self.population)):
            for j in range(i + 1, len(self.population)):
                distance = self._genetic_distance(self.population[i], self.population[j])
                diversity += distance
                comparisons += 1

        return diversity / comparisons if comparisons > 0 else 0.0

    def express_genome_as_protocol(self, genome: ProtocolGenome,
                                  template: Optional
