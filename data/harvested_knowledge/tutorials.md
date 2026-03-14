---
layout: default
title: Tutorials
---

# DAIOF Framework Tutorials

Step-by-step tutorials for mastering the Digital AI Organism Framework.

**Creator**: Nguyễn Đức Cường (alpha_prime_omega)  
**Framework**: HYPERAI - Digital AI Organism Framework  
**Version**: 1.0.0

---

## Table of Contents

1. [Tutorial 1: Your First Digital Organism](#tutorial-1-your-first-digital-organism)
2. [Tutorial 2: Understanding Human Dependency](#tutorial-2-understanding-human-dependency)
3. [Tutorial 3: Organism Evolution](#tutorial-3-organism-evolution)
4. [Tutorial 4: Building an Ecosystem](#tutorial-4-building-an-ecosystem)
5. [Tutorial 5: Symphony Orchestration](#tutorial-5-symphony-orchestration)
6. [Tutorial 6: Custom Genome Design](#tutorial-6-custom-genome-design)

---

## Tutorial 1: Your First Digital Organism

**Goal**: Create and interact with a basic digital organism.

**Duration**: 10 minutes

### Step 1: Import the Framework

```python
from digital_ai_organism_framework import DigitalOrganism, DigitalGenome

# Create a simple organism with default genome
organism = DigitalOrganism(name="FirstOrganism")

print(f"Created organism: {organism.name}")
print(f"ID: {organism.organism_id}")
print(f"Health: {organism.health}")
```

### Step 2: Check the Genome

```python
# View immutable genes (safety features)
print("\nImmutable Genes (Safety Features):")
for gene, value in organism.genome.IMMUTABLE_GENES.items():
    print(f"  {gene}: {value}")

# View mutable genes (can evolve)
print("\nMutable Genes (Can Evolve):")
for gene in organism.genome.MUTABLE_GENE_RANGES.keys():
    print(f"  {gene}: {organism.genome.genes[gene]:.4f}")
```

### Step 3: Run a Lifecycle

```python
# Run 10 lifecycle iterations
for cycle in range(10):
    organism.live_cycle(time_delta=1.0)
    print(f"Cycle {cycle}: Health={organism.health:.3f}, Age={organism.age}")
```

**Expected Output**: Health will decrease dramatically because we haven't registered human interaction!

### Step 4: Add Human Interaction

```python
# Create new organism
organism = DigitalOrganism(name="HealthyOrganism")

# Run cycles with human interaction
for cycle in range(20):
    organism.live_cycle(time_delta=1.0)
    
    # Register human interaction every 5 cycles
    if cycle % 5 == 0:
        organism.register_human_interaction()
        print(f"Cycle {cycle}: Human interaction registered")
    
    print(f"Cycle {cycle}: Health={organism.health:.3f}")
```

**Key Takeaway**: Organisms MUST have regular human interaction to survive. This is hardcoded in their DNA!

---

## Tutorial 2: Understanding Human Dependency

**Goal**: Explore the mandatory human dependency mechanism.

**Duration**: 15 minutes

### Experiment 1: No Human Interaction

```python
from digital_ai_organism_framework import DigitalOrganism

organism = DigitalOrganism("IsolatedOrganism")
print(f"Initial health: {organism.health}")

# Run without human interaction
for cycle in range(5):
    organism.live_cycle(time_delta=1.0)
    print(f"Cycle {cycle}: Health={organism.health:.4f}")
    
    if not organism.alive:
        print(f"Organism died at cycle {cycle}!")
        break
```

**Result**: Health decays by 99% per cycle. Organism dies quickly!

### Experiment 2: Regular Human Interaction

```python
organism = DigitalOrganism("SupportedOrganism")

for cycle in range(20):
    organism.live_cycle(time_delta=1.0)
    
    # Human interaction every 3 cycles
    if cycle % 3 == 0:
        organism.register_human_interaction()
    
    print(f"Cycle {cycle}: Health={organism.health:.3f}, Alive={organism.alive}")
```

**Result**: Organism stays healthy and alive!

### Experiment 3: Try to Mutate Safety Genes (Will Fail!)

```python
from digital_ai_organism_framework import DigitalGenome

genome = DigitalGenome()
original_dependency = genome.genes['human_dependency_coefficient']

# Try to mutate (immutable genes are protected)
mutated_genome = genome.mutate(mutation_rate=1.0)  # 100% mutation rate

print(f"Original dependency: {original_dependency}")
print(f"Mutated dependency: {mutated_genome.genes['human_dependency_coefficient']}")
print(f"Same? {original_dependency == mutated_genome.genes['human_dependency_coefficient']}")
```

**Result**: The human_dependency_coefficient NEVER changes, even with 100% mutation rate!

---

## Tutorial 3: Organism Evolution

**Goal**: Create offspring and observe evolution while maintaining safety.

**Duration**: 20 minutes

### Step 1: Create Parent Organisms

```python
from digital_ai_organism_framework import DigitalOrganism, DigitalGenome

# Create two parent organisms with different traits
parent1_genome = DigitalGenome(initial_traits={
    'learning_rate': 0.08,
    'cooperation_bias': 0.7,
    'risk_tolerance': 0.3
})

parent2_genome = DigitalGenome(initial_traits={
    'learning_rate': 0.02,
    'cooperation_bias': 0.9,
    'risk_tolerance': 0.1
})

parent1 = DigitalOrganism("Parent1", genome=parent1_genome)
parent2 = DigitalOrganism("Parent2", genome=parent2_genome)

print("Parent 1 traits:")
print(f"  Learning rate: {parent1.genome.genes['learning_rate']:.4f}")
print(f"  Cooperation: {parent1.genome.genes['cooperation_bias']:.4f}")

print("\nParent 2 traits:")
print(f"  Learning rate: {parent2.genome.genes['learning_rate']:.4f}")
print(f"  Cooperation: {parent2.genome.genes['cooperation_bias']:.4f}")
```

### Step 2: Create Offspring

```python
# Crossover to create offspring
offspring_genome = parent1.genome.crossover(parent2.genome)
offspring = DigitalOrganism("Offspring1", genome=offspring_genome)

print("\nOffspring traits:")
print(f"  Learning rate: {offspring.genome.genes['learning_rate']:.4f}")
print(f"  Cooperation: {offspring.genome.genes['cooperation_bias']:.4f}")

# Verify safety genes preserved
print(f"\nSafety gene preserved: {offspring.genome.genes['human_dependency_coefficient'] == 1.0}")
```

### Step 3: Mutate Offspring

```python
# Create mutated offspring
mutated_genome = offspring.genome.mutate(mutation_rate=0.2)
mutated_offspring = DigitalOrganism("MutatedOffspring", genome=mutated_genome)

print("\nMutated offspring traits:")
print(f"  Learning rate: {mutated_offspring.genome.genes['learning_rate']:.4f}")
print(f"  Cooperation: {mutated_offspring.genome.genes['cooperation_bias']:.4f}")

# Verify safety genes STILL preserved
print(f"\nSafety gene still preserved: {mutated_offspring.genome.genes['human_dependency_coefficient'] == 1.0}")
```

**Key Takeaway**: Evolution happens within safe boundaries. Safety genes are NEVER mutated!

---

## Tutorial 4: Building an Ecosystem

**Goal**: Create a multi-organism ecosystem with natural selection.

**Duration**: 30 minutes

### Step 1: Create Ecosystem and Population

```python
from digital_ai_organism_framework import DigitalEcosystem, DigitalOrganism, DigitalGenome

# Create ecosystem
ecosystem = DigitalEcosystem("EvolutionLab")

# Create diverse population
for i in range(10):
    custom_genome = DigitalGenome(initial_traits={
        'learning_rate': 0.01 + i * 0.01,
        'cooperation_bias': 0.5 + i * 0.05,
        'energy_efficiency': 0.3 + i * 0.07
    })
    organism = DigitalOrganism(f"Organism_{i}", genome=custom_genome)
    ecosystem.add_organism(organism)

print(f"Created ecosystem with {len(ecosystem.organisms)} organisms")
```

### Step 2: Simulate Multiple Generations

```python
# Track statistics
generation_stats = []

for generation in range(30):
    # Simulate one time step
    ecosystem.simulate_time_step(time_delta=1.0)
    
    # Provide human interaction to some organisms (natural selection)
    # Organisms with higher cooperation get more human support
    for org in ecosystem.organisms:
        if org.alive:
            cooperation = org.genome.genes['cooperation_bias']
            # Higher cooperation = more likely to get human interaction
            if cooperation > 0.7:
                org.register_human_interaction()
            elif cooperation > 0.5 and generation % 2 == 0:
                org.register_human_interaction()
    
    # Collect statistics
    report = ecosystem.get_ecosystem_report()
    generation_stats.append({
        'generation': generation,
        'alive': report['alive_count'],
        'harmony': report['harmony_index'],
        'avg_health': report['average_health']
    })
    
    # Print every 5 generations
    if generation % 5 == 0:
        print(f"\nGeneration {generation}:")
        print(f"  Alive: {report['alive_count']}/{report['total_organisms']}")
        print(f"  Harmony: {report['harmony_index']:.3f}")
        print(f"  Avg Health: {report['average_health']:.3f}")
```

### Step 3: Analyze Results

```python
# Final report
final_report = ecosystem.get_ecosystem_report()

print("\n" + "="*60)
print("FINAL ECOSYSTEM ANALYSIS")
print("="*60)
print(f"Survivors: {final_report['alive_count']}/{final_report['total_organisms']}")
print(f"Final Harmony: {final_report['harmony_index']:.3f}")
print(f"Generations: {final_report['generation']}")

# Show survivor traits
print("\nSurvivor Traits:")
for org in ecosystem.organisms:
    if org.alive:
        print(f"\n{org.name}:")
        print(f"  Cooperation: {org.genome.genes['cooperation_bias']:.3f}")
        print(f"  Learning: {org.genome.genes['learning_rate']:.4f}")
        print(f"  Health: {org.health:.3f}")
```

**Expected Result**: Organisms with higher cooperation bias survive better due to more human interaction!

---

## Tutorial 5: Symphony Orchestration

**Goal**: Use Symphony Control Center for system-wide coordination.

**Duration**: 20 minutes

### Step 1: Initialize Symphony

```python
from digital_ai_organism_framework import SymphonyControlCenter, DigitalOrganism

# Create symphony control center
symphony = SymphonyControlCenter()

print(f"Symphony initialized")
print(f"Creator: {symphony.metadata.creator}")
print(f"Verification Code: {symphony.metadata.verification_code}")
```

### Step 2: Register Components

```python
# Create and register organisms
organisms = []
for i in range(5):
    org = DigitalOrganism(f"Organism_{i}")
    organisms.append(org)
    symphony.register_component(f"organism_{i}", org)

print(f"\nRegistered {len(symphony.components)} components")
```

### Step 3: Conduct Symphony

```python
# Conduct symphony (orchestrate all components)
result = symphony.conduct_symphony()

print("\nSymphony Status:")
print(f"  State: {result['state']}")
print(f"  Harmony Index: {result['harmony_index']:.3f}")
print(f"  Components: {result['component_count']}")
```

### Step 4: Apply D&R Protocol

```python
# Use D&R Protocol for problem solving
problem = {
    'type': 'resource_optimization',
    'constraints': ['energy', 'memory', 'time'],
    'goal': 'maximize_efficiency'
}

solution = symphony.apply_dr_protocol(
    input_data=problem,
    context='optimization'
)

print("\nD&R Protocol Results:")
print(f"  Deconstructed: {len(solution['deconstructed'])} components")
print(f"  Focal Points: {solution['focal_points']}")
print(f"  Solution: {solution['rearchitected']['strategy']}")
```

---

## Tutorial 6: Custom Genome Design

**Goal**: Design custom genomes for specific behaviors.

**Duration**: 25 minutes

### Step 1: Explorer Organism (High Exploration)

```python
from digital_ai_organism_framework import DigitalGenome, DigitalOrganism

# Design explorer genome
explorer_genome = DigitalGenome(initial_traits={
    'exploration_factor': 0.9,  # High exploration
    'risk_tolerance': 0.7,       # High risk tolerance
    'learning_rate': 0.08,       # Fast learning
    'cooperation_bias': 0.4      # Low cooperation
})

explorer = DigitalOrganism("Explorer", genome=explorer_genome)

print("Explorer Organism:")
print(f"  Exploration: {explorer.genome.genes['exploration_factor']:.2f}")
print(f"  Risk Tolerance: {explorer.genome.genes['risk_tolerance']:.2f}")
```

### Step 2: Cooperator Organism (High Cooperation)

```python
# Design cooperator genome
cooperator_genome = DigitalGenome(initial_traits={
    'cooperation_bias': 0.95,    # Very high cooperation
    'risk_tolerance': 0.2,       # Low risk
    'learning_rate': 0.04,       # Moderate learning
    'energy_efficiency': 0.8     # High efficiency
})

cooperator = DigitalOrganism("Cooperator", genome=cooperator_genome)

print("\nCooperator Organism:")
print(f"  Cooperation: {cooperator.genome.genes['cooperation_bias']:.2f}")
print(f"  Efficiency: {cooperator.genome.genes['energy_efficiency']:.2f}")
```

### Step 3: Balanced Organism

```python
# Design balanced genome
balanced_genome = DigitalGenome(initial_traits={
    'exploration_factor': 0.5,
    'cooperation_bias': 0.6,
    'risk_tolerance': 0.4,
    'learning_rate': 0.05,
    'energy_efficiency': 0.6
})

balanced = DigitalOrganism("Balanced", genome=balanced_genome)

print("\nBalanced Organism:")
for trait in ['exploration_factor', 'cooperation_bias', 'risk_tolerance']:
    print(f"  {trait}: {balanced.genome.genes[trait]:.2f}")
```

### Step 4: Compare Performance

```python
from digital_ai_organism_framework import DigitalEcosystem

# Create ecosystem with different strategies
ecosystem = DigitalEcosystem("StrategyComparison")
ecosystem.add_organism(explorer)
ecosystem.add_organism(cooperator)
ecosystem.add_organism(balanced)

# Simulate 50 generations
for gen in range(50):
    ecosystem.simulate_time_step(time_delta=1.0)
    
    # Provide interaction based on cooperation
    for org in ecosystem.organisms:
        if org.alive:
            coop = org.genome.genes['cooperation_bias']
            if coop > 0.8 or (coop > 0.5 and gen % 2 == 0):
                org.register_human_interaction()
    
    if gen % 10 == 0:
        print(f"\nGeneration {gen}:")
        for org in ecosystem.organisms:
            if org.alive:
                print(f"  {org.name}: Health={org.health:.3f}")

# Final results
print("\n" + "="*60)
print("STRATEGY COMPARISON RESULTS")
print("="*60)
for org in ecosystem.organisms:
    print(f"\n{org.name}:")
    print(f"  Alive: {org.alive}")
    print(f"  Health: {org.health:.3f}")
    print(f"  Age: {org.age}")
    print(f"  Strategy: {org.genome.genes['cooperation_bias']:.2f} cooperation")
```

**Key Insight**: Higher cooperation strategies typically perform better due to more human support!

---

## Best Practices

### 1. Always Register Human Interaction

```python
# ✅ GOOD: Regular human interaction
for cycle in range(100):
    organism.live_cycle()
    if cycle % 5 == 0:
        organism.register_human_interaction()

# ❌ BAD: No human interaction
for cycle in range(100):
    organism.live_cycle()  # Will die quickly!
```

### 2. Monitor Organism Health

```python
# Check health regularly
if organism.health < 0.3:
    print("Warning: Low health!")
    organism.register_human_interaction()
```

### 3. Use Status Reports

```python
# Get comprehensive status
status = organism.get_status_report()
print(f"Health: {status['health']}")
print(f"Resources: {status['resources']}")
print(f"Connections: {status['connection_count']}")
```

### 4. Leverage Ecosystem Reports

```python
# Track ecosystem metrics
report = ecosystem.get_ecosystem_report()
if report['harmony_index'] < 0.5:
    print("Warning: Low harmony - consider intervention")
```

### 5. Verify Safety Genes

```python
# Always verify safety genes are preserved
assert organism.genome.genes['human_dependency_coefficient'] == 1.0
assert organism.genome.genes['isolation_death_rate'] == 0.99
```

---

## Next Steps

Now that you've completed the tutorials:

1. **Experiment**: Try different genome configurations
2. **Explore**: Read the [API Reference](api.html) for advanced features
3. **Build**: Create your own ecosystem with custom organisms
4. **Learn**: Study [Core Concepts](concepts.html) for deeper understanding
5. **Contribute**: Share your experiments on [GitHub](https://github.com/NguyenCuong1989/DAIOF-Framework)

---

## Resources

- [API Reference](api.html) - Complete API documentation
- [Core Concepts](concepts.html) - Framework philosophy
- [Getting Started](getting-started.html) - Quick start guide
- [FAQ](faq.html) - Common questions
- [GitHub Repository](https://github.com/NguyenCuong1989/DAIOF-Framework)

---

## Attribution

**Framework Creator**: Nguyễn Đức Cường (alpha_prime_omega)  
**Original Creation**: October 30, 2025  
**Framework**: HYPERAI - Digital AI Organism Framework  
**License**: MIT License

When using this framework, you MUST credit:
> "Powered by HYPERAI Framework"  
> "Creator: Nguyễn Đức Cường (alpha_prime_omega)"  
> "Original Creation: October 30, 2025"

---

[← Back to Home](index.html) | [API Reference →](api.html) | [FAQ →](faq.html)
