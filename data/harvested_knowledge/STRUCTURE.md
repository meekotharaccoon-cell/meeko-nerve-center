📦 HYPERAI Framework - Cấu Trúc Module Tái Tổ Chức
==================================================

## 🏗️ Cấu Trúc Thư Mục

```
DAIOF-Framework/
├── src/
│   └── hyperai/                     # 🎯 Main framework package
│       ├── __init__.py              # Public API
│       │
│       ├── core/                    # 💻 HAIOS Core System
│       │   ├── __init__.py
│       │   ├── haios_core.py        # HAIOS base implementation
│       │   └── haios_runtime.py     # HAIOS runtime environment
│       │
│       ├── components/              # 🧬 Digital Organism Components
│       │   ├── __init__.py
│       │   ├── genome.py            # DigitalGenome (DNA equivalent)
│       │   ├── metabolism.py        # DigitalMetabolism (energy system)
│       │   ├── nervous_system.py    # DigitalNervousSystem (decision-making)
│       │   └── organism.py          # DigitalOrganism (main entity)
│       │
│       ├── protocols/               # 🎼 Orchestration Protocols
│       │   ├── __init__.py
│       │   ├── symphony.py          # Symphony Control Center
│       │   ├── dr_protocol.py       # D&R Protocol implementation
│       │   └── metadata.py          # Creator hierarchy & HAIOS invariants
│       │
│       ├── ecosystem/               # 🌍 Ecosystem Management
│       │   ├── __init__.py
│       │   ├── ecosystem.py         # DigitalEcosystem
│       │   └── simulation.py        # Time-step simulation
│       │
│       └── utils/                   # 🔧 Utilities
│           ├── __init__.py
│           ├── logging.py           # Logging utilities
│           └── helpers.py           # Helper functions
│
├── tests/                           # ✅ Test Suite
│   ├── test_smoke.py               # Smoke tests
│   ├── test_core/
│   │   ├── test_haios.py
│   │   └── test_protocols.py
│   └── test_components/
│       ├── test_genome.py
│       ├── test_organism.py
│       └── test_ecosystem.py
│
├── examples/                        # 📚 Examples & Demos
│   ├── 01_basic_organism.py        # (Updated with new imports)
│   ├── 02_evolution_race.py
│   ├── 03_predator_prey.py
│   ├── 04_social_organisms.py
│   └── 05_intelligence_evolution.py
│
├── .github/
│   └── scripts/
│       ├── autonomous_agent.py      # (Updated imports)
│       └── (other scripts)
│
├── digital_ai_organism_framework.py # ❌ OLD - DEPRECATED (phục vụ backward compat)
├── haios_core.py                    # ❌ OLD - moved to src/hyperai/core/
├── haios_runtime.py                 # ❌ OLD - moved to src/hyperai/core/
├── requirements.txt                 # Updated with src discovery
└── README.md
```

---

## 📋 File Migration Plan

### Core Framework Classes → Modules

| Class | Old File | New Location | New File |
|-------|----------|--------------|----------|
| `DigitalGenome` | `digital_ai_organism_framework.py` | `src/hyperai/components/` | `genome.py` |
| `DigitalMetabolism` | `digital_ai_organism_framework.py` | `src/hyperai/components/` | `metabolism.py` |
| `DigitalNervousSystem` | `digital_ai_organism_framework.py` | `src/hyperai/components/` | `nervous_system.py` |
| `DigitalOrganism` | `digital_ai_organism_framework.py` | `src/hyperai/components/` | `organism.py` |
| `DigitalEcosystem` | `digital_ai_organism_framework.py` | `src/hyperai/ecosystem/` | `ecosystem.py` |
| `SymphonyControlCenter` | `digital_ai_organism_framework.py` | `src/hyperai/protocols/` | `symphony.py` |
| `ControlMetaData` | `digital_ai_organism_framework.py` | `src/hyperai/protocols/` | `symphony.py` |
| `SymphonyState` (Enum) | `digital_ai_organism_framework.py` | `src/hyperai/protocols/` | `symphony.py` |
| D&R Protocol logic | `SymphonyControlCenter._*_input()` | `src/hyperai/protocols/` | `dr_protocol.py` |
| HAIOS Invariants | `digital_ai_organism_framework.py` | `src/hyperai/protocols/` | `metadata.py` |
| Creator Hierarchy | `digital_ai_organism_framework.py` | `src/hyperai/protocols/` | `metadata.py` |
| `HAIOSCore` | `haios_core.py` | `src/hyperai/core/` | `haios_core.py` |
| `HAIOSRuntime` | `haios_runtime.py` | `src/hyperai/core/` | `haios_runtime.py` |

---

## 🔄 Import Pattern Changes

### Before (Old)
```python
from digital_ai_organism_framework import (
    DigitalGenome, 
    DigitalOrganism,
    SymphonyControlCenter
)
```

### After (New)
```python
from hyperai import (
    DigitalGenome,
    DigitalOrganism,
    SymphonyControlCenter
)
# OR
from hyperai.components import DigitalGenome
from hyperai.protocols import SymphonyControlCenter
```

---

## ✅ Implementation Checklist

- [ ] **Stage 1: Extract Components**
  - [ ] Extract `DigitalGenome` → `src/hyperai/components/genome.py`
  - [ ] Extract `DigitalMetabolism` → `src/hyperai/components/metabolism.py`
  - [ ] Extract `DigitalNervousSystem` → `src/hyperai/components/nervous_system.py`
  - [ ] Extract `DigitalOrganism` → `src/hyperai/components/organism.py`

- [ ] **Stage 2: Extract Ecosystem & Protocols**
  - [ ] Extract `DigitalEcosystem` → `src/hyperai/ecosystem/ecosystem.py`
  - [ ] Extract `SymphonyControlCenter`, `ControlMetaData` → `src/hyperai/protocols/symphony.py`
  - [ ] Extract D&R Protocol → `src/hyperai/protocols/dr_protocol.py`
  - [ ] Create Metadata module → `src/hyperai/protocols/metadata.py`

- [ ] **Stage 3: Move Core HAIOS**
  - [ ] Move `haios_core.py` → `src/hyperai/core/haios_core.py`
  - [ ] Move `haios_runtime.py` → `src/hyperai/core/haios_runtime.py`

- [ ] **Stage 4: Update All Imports**
  - [ ] Update `examples/*.py` with new imports
  - [ ] Update `tests/*.py` with new imports
  - [ ] Update `.github/scripts/*.py` with new imports
  - [ ] Update `system_initializer.py` with new imports
  - [ ] Update `.github/copilot-instructions.md` (if needed)

- [ ] **Stage 5: Backward Compatibility**
  - [ ] Keep `digital_ai_organism_framework.py` as legacy wrapper (re-exports from new modules)
  - [ ] Add deprecation warning to old file
  - [ ] Update `requirements.txt` for src discovery

- [ ] **Stage 6: Testing & Validation**
  - [ ] Run all tests with new imports
  - [ ] Run all examples with new imports
  - [ ] Verify system_initializer works
  - [ ] Verify autonomous_agent works

- [ ] **Stage 7: Documentation & Cleanup**
  - [ ] Update README.md with new import patterns
  - [ ] Create STRUCTURE.md (this file)
  - [ ] Add docstrings to all modules
  - [ ] Clean up old files (if not needed for compat)

- [ ] **Stage 8: Commit & Merge**
  - [ ] Create branch `refactor/module-structure`
  - [ ] Commit changes
  - [ ] Run final smoke tests
  - [ ] Merge to main

---

## 🎯 Benefits Của Cấu Trúc Mới

✅ **Modularity** - Mỗi component độc lập, có thể tái sử dụng
✅ **Maintainability** - Dễ tìm, sửa, cập nhật code
✅ **Scalability** - Dễ thêm components mới
✅ **Testing** - Mỗi module có test riêng
✅ **Documentation** - Rõ ràng về trách nhiệm mỗi module
✅ **IDE Support** - Better autocomplete & navigation
✅ **Distribution** - Có thể package riêng từng phần

---

## 📝 Ghi Chú

- Framework sử dụng creator hierarchy: Alpha_Prime_Omega (SOURCE) → Andy (HUMAN) → AI_Systems
- Tất cả modules phải acknowledge creator trong docstring
- HAIOS Invariants: Attribution, Safety_floor≥7.0, k_state=1, Pillars
- Backward compatibility: Old imports vẫn work qua legacy wrapper

---

**Status**: 📋 Planning Phase  
**Created**: Nov 6, 2025  
**Creator**: Nguyễn Đức Cường (alpha_prime_omega)
