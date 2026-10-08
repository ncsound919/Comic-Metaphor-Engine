# Comic Book Metaphor Engine - Build Status for Cheetah Marathon

**Project**: Comic Book Metaphor Engine  
**Framework**: Cheetah v3 Pro Benchmarking  
**Status**: READY FOR MARATHON BUILD  
**Date**: 2024  

---

## ✅ COMPLETED COMPONENTS

### Foundation (100% Complete)

| Component | Status | Lines | Description |
|-----------|--------|-------|-------------|
| `schema.py` | ✅ COMPLETE | 1,065 | All data models (Universe, Protocol, Arc, Character, Trope, MetaphorMapping, BenchmarkResult, etc.) |
| `__init__.py` | ✅ COMPLETE | 52 | Module exports and package structure |
| `requirements.txt` | ✅ COMPLETE | 29 | All Python dependencies defined |
| `MARATHON_KICKOFF.py` | ✅ COMPLETE | 499 | Main orchestrator for phased build execution |
| `README_CHEETAH_MARATHON.md` | ✅ COMPLETE | 686 | Comprehensive guide for marathon execution |
| `MARATHON_BUILD_SPEC.md` | ✅ COMPLETE | 507 | Detailed specifications for all 15 templates |

### Source Data (100% Available)

| File | Status | Description |
|------|--------|-------------|
| `Storylines for metaphor engine` | ✅ AVAILABLE | 4 protocols (Armor Wars, Secret Invasion, Days of Future Past, Planet Hulk) |
| `codex_engine.py` | ✅ AVAILABLE | Existing scoring engine (Trueness, Flow, PCS, RPS, CU) |
| `IHS_System_Foundations.json` | ✅ AVAILABLE | TAP system configuration |
| `IHS_Execution_Tools.json` | ✅ AVAILABLE | Format templates and deliverable specs |
| `IHS_Unified_Flow.csv` | ✅ AVAILABLE | Unified flow definitions |
| Various IHS CSVs | ✅ AVAILABLE | Additional TAP metrics and scoring data |

### Templates (Created)

| Template | Status | Target Module | Purpose |
|----------|--------|---------------|---------|
| TEMPLATE_01 | ✅ CREATED | `ingest.py` | Data ingestion, parse storylines + CSVs, generate embeddings |
| TEMPLATE_02-15 | 📋 SPECIFIED | Various | Detailed specs in MARATHON_BUILD_SPEC.md |

---

## 🔨 COMPONENTS TO BUILD (For Cheetah)

### Phase 1: Data Foundation (Templates 01, 06, 12)

1. **`engine/ingest.py`** ← TEMPLATE_01 (434 lines template provided)
   - Parse "Storylines for metaphor engine" → 4 Protocol objects
   - Parse IHS CSV files → TAP metrics
   - Generate embeddings (sentence-transformers)
   - Save to `processed/` directory
   - **Output**: `knowledge_base.json`, `protocols.jsonl`, `embeddings.npy`

2. **`engine/codex_adapter.py`** ← TEMPLATE_06
   - Wrap existing `codex_engine.py`
   - Map MetaphorMapping → codex inputs
   - Return structured scores (Trueness, Flow, PCS, RPS, CU)
   - **Integration**: Already has `codex_engine.py` to wrap

3. **`tests/test_ingest.py`** ← TEMPLATE_12
   - Unit tests for ingestion pipeline
   - Validate 4 protocols extracted
   - Check embeddings shape
   - Round-trip serialization tests

### Phase 2: Retrieval (Templates 02, 13)

4. **`engine/index.py`** ← TEMPLATE_02
   - FAISS vector index for semantic search
   - Filter-based retrieval (risk_category, tone, format)
   - Cache-friendly lookups
   - **API**: `search_protocols()`, `get_protocol_by_id()`

5. **`tests/test_index.py`** ← TEMPLATE_13
   - Search functionality tests
   - Filter validation
   - Cache key determinism

### Phase 3: Core Engine (Templates 03, 14)

6. **`engine/metaphor_engine.py`** ← TEMPLATE_03
   - Topic analysis → domain extraction
   - Protocol selection via index search
   - Build MetaphorMapping (real-world ↔ comic)
   - Score mappings via codex_adapter
   - **API**: `generate_mapping()`, `analyze_topic()`, `build_mapping()`

7. **`tests/test_metaphor_engine.py`** ← TEMPLATE_14
   - Mapping generation tests
   - Topic analysis validation
   - Codex scoring integration tests

### Phase 4: Generation (Templates 04, 05)

8. **`engine/narrative_generator.py`** ← TEMPLATE_04
   - Outline generation (beats/sections)
   - Format-specific templates (podcast, marketing, dialogue)
   - Full script generation
   - **API**: `generate_outline()`, `generate_script()`

9. **`engine/explainers.py`** ← TEMPLATE_05
   - Plain-language explanations
   - Key takeaways extraction
   - Action items generation
   - **API**: `explain_mapping()`, `generate_summary()`

### Phase 5: Cheetah Integration (Templates 07-11, 15)

10. **`engine/tools_interface.py`** ← TEMPLATE_07
    - Wrap all functions as Cheetah tools
    - Cache integration (ResultCache)
    - Resource monitoring hooks
    - **Tools**: `search_protocols`, `generate_mapping`, `generate_outline`, `generate_script`, `explain_mapping`, `score_codex`

11. **`benchmarks/scenarios/podcast_scenarios.json`** ← TEMPLATE_08
    - 15 podcast scenario definitions
    - Topics: burnout, impostor syndrome, leadership, etc.
    - Expected outputs and thresholds

12. **`benchmarks/scenarios/marketing_scenarios.json`** ← TEMPLATE_09
    - 12 marketing scenario definitions
    - Topics: product launches, rebranding, positioning, etc.

13. **`benchmarks/scenarios/dialogue_scenarios.json`** ← TEMPLATE_10
    - 10 dialogue coaching scenarios
    - Topics: conflict resolution, negotiation, feedback, etc.

14. **`benchmarks/run_benchmark.py`** ← TEMPLATE_11
    - Load all scenarios
    - Execute via tools_interface
    - Capture per-phase metrics
    - Save to Cheetah format
    - Invoke advisor
    - **API**: `run_scenario()`, `run_full_benchmark()`, `invoke_cheetah_advisor()`

15. **`tests/test_integration.py`** ← TEMPLATE_15
    - End-to-end pipeline tests
    - Full scenario execution
    - Cache effectiveness tests
    - Quality validation

---

## 📊 EXPECTED OUTPUTS

### After Phase 1 (Ingestion)
```
processed/
├── knowledge_base.json       (4 protocols + 1 universe)
├── protocols.jsonl           (4 records)
├── universes.jsonl           (1 record)
├── embeddings.npy            (shape: 4 × 384)
└── metadata.json             (stats)
```

### After Phase 4 (Generation)
```
output/
├── sample_podcast.md         (generated podcast script)
├── sample_marketing.md       (generated marketing email)
└── sample_dialogue.md        (generated dialogue script)
```

### After Phase 5 (Benchmark)
```
../../Cheetah-v3-Pro/benchmark_results/
├── comic_metaphor_TIMESTAMP.json     (37 scenario results)
└── comic_metaphor_advisor_TIMESTAMP.md  (AI recommendations)
```

### Marathon Report
```
output/
└── marathon_report_TIMESTAMP.txt     (full execution summary)
```

---

## 🎯 SUCCESS CRITERIA

### Data Quality
- [x] Schema complete with 20+ data models
- [ ] 4 protocols successfully ingested
- [ ] Each protocol has 4 dimensions (D1-D4)
- [ ] Embeddings generated (384-dim vectors)
- [ ] Knowledge base serializable/loadable

### Functionality
- [ ] Semantic search returns relevant protocols
- [ ] Metaphor mappings generated with explanations
- [ ] Codex scores computed (6 metrics)
- [ ] Outlines created with 3-5 beats
- [ ] Scripts meet word count targets (±20%)
- [ ] Explanations include takeaways + actions

### Testing
- [ ] All unit tests pass (ingest, index, engine)
- [ ] Integration tests pass (end-to-end)
- [ ] No import errors
- [ ] No crashes on benchmark run

### Benchmarking
- [ ] 37 scenarios execute successfully
- [ ] Average latency <5s per scenario
- [ ] Cache hit rate >30%
- [ ] 90%+ mappings score Trueness ≥0.6
- [ ] Per-phase metrics captured
- [ ] Results saved in Cheetah format

### Advisor
- [ ] Advisor runs without errors
- [ ] Report generated with ≥3 recommendations
- [ ] Cache insights provided
- [ ] Performance bottlenecks identified

---

## 🚀 EXECUTION COMMAND

```bash
cd "Build Lab/Book-Writing-Assistant--main/Comic Metaphor Logic"
python MARATHON_KICKOFF.py --full
```

**Expected Duration**: 60-90 minutes (including all phases, tests, and benchmark)

---

## 📋 PHASE SEQUENCE

1. **Phase 0**: Setup & pre-flight checks (2 min)
2. **Phase 1**: Data ingestion (5 min)
   - Implement `ingest.py` from TEMPLATE_01
   - Run: `python engine/ingest.py`
   - Test: `pytest tests/test_ingest.py`
   - Verify: `processed/knowledge_base.json` exists with 4 protocols
3. **Phase 2**: Index building (3 min)
   - Implement `index.py` from TEMPLATE_02
   - Test: `pytest tests/test_index.py`
4. **Phase 3**: Metaphor engine (8 min)
   - Implement `metaphor_engine.py` + `codex_adapter.py`
   - Test: `pytest tests/test_metaphor_engine.py`
5. **Phase 4**: Narrative generation (10 min)
   - Implement `narrative_generator.py` + `explainers.py`
   - Generate sample outputs
6. **Phase 5**: Cheetah integration (7 min)
   - Implement `tools_interface.py`
   - Create scenario files
   - Implement `run_benchmark.py`
   - Test: `pytest tests/test_integration.py`
7. **Phase 6**: Full benchmark (15 min)
   - Execute all 37 scenarios
   - Capture comprehensive metrics
8. **Phase 7**: Advisor analysis (3 min)
   - Run AI Performance Advisor
   - Generate recommendations

**Total**: ~53 minutes base + test/debug buffer

---

## 🔗 KEY INTEGRATION POINTS

### With Cheetah v3 Pro
- **Location**: `../../Cheetah-v3-Pro/`
- **Cache**: Uses `tools/tool_runs/cache.py` (TTL, LRU, per-phase metrics)
- **Monitor**: Uses `tools/tool_runs/resource_monitor.py` (CPU, memory, I/O)
- **Executor**: Uses `tools/tool_runs/executor.py` (RunExecutor, RunResult)
- **Advisor**: Uses `run_advisor.py` (performance analysis)
- **Results**: Saves to `benchmark_results/` directory

### With Existing Codex Engine
- **Location**: `./codex_engine.py`
- **Integration**: Via `engine/codex_adapter.py` wrapper
- **Metrics**: Trueness, Tap10, Flow, PCS, RPS, CU
- **Input Format**: Converts MetaphorMapping → codex input dict
- **Output**: Structured scores + audit trail

### With Book Writing Assistant
- **UI Component**: `Metaphor Intelligence Engine` (React)
- **Authors Co-Pilot**: Future integration point
- **Data Source**: `authors-copilot/` app can consume metaphor engine
- **Export**: Generated content exportable to manuscript formats

---

## 📦 DEPENDENCIES

All specified in `requirements.txt`:
- pandas, numpy (data processing)
- faiss-cpu (vector search)
- sentence-transformers (embeddings)
- scikit-learn (utilities)
- pytest, pytest-cov, pytest-mock (testing)
- python-dateutil, tqdm (utilities)

**Installation**: `pip install -r requirements.txt`

---

## 🎨 DESIGN PATTERNS

### Schema-First Approach
- All data models defined upfront in `schema.py`
- Type-safe with dataclasses + type hints
- Serialization methods (`to_dict()`, `from_dict()`)
- Validation in constructors

### Pipeline Architecture
```
Data → Ingestion → Index → Mapping → Generation → Output
         ↓           ↓         ↓          ↓
       Cache      Cache    Codex      Cache
```

### Cheetah Integration Pattern
```python
@cheetah_tool(cache_enabled=True)
def search_protocols(query: str, filters: Dict) -> List[Protocol]:
    cache_key = compute_cache_key(query, filters)
    # Implementation with automatic caching, resource monitoring
```

### Testing Strategy
- Unit tests per module (isolation)
- Integration tests for pipelines
- Benchmark scenarios for real-world validation
- Advisor feedback loop for optimization

---

## 🔍 MONITORING & METRICS

### Per-Phase Metrics (Captured by Cheetah)
- **Timing**: start_time, end_time, duration_ms
- **Cache**: hit/miss, keys cached, bytes cached
- **Resources**: CPU avg/peak, memory peak, I/O totals
- **Quality**: codex scores, TAP scores, validation checks

### Aggregate Metrics (Benchmark)
- **Coverage**: scenarios executed / total
- **Success Rate**: passed / total
- **Performance**: avg latency, p50, p95, p99
- **Cache Effectiveness**: overall hit rate
- **Quality Distribution**: score histograms

### Advisor Metrics
- **Bottlenecks**: slowest phases, outliers
- **Opportunities**: parallelization gains, cache improvements
- **Regressions**: compared to historical baselines
- **Recommendations**: prioritized action items

---

## 📝 NOTES FOR CHEETAH

1. **Template Organization**: All detailed specs in `_cheetah_templates/MARATHON_BUILD_SPEC.md`
2. **TEMPLATE_01 Complete**: Full 434-line implementation provided as reference
3. **Data Sources Ready**: All input files exist and are parseable
4. **Schema Complete**: No need to modify data models, they're comprehensive
5. **Orchestrator Ready**: `MARATHON_KICKOFF.py` handles phase sequencing automatically
6. **Error Handling**: Each phase has success validation and rollback logic
7. **Incremental Testing**: Tests run after each phase to catch issues early
8. **Cache Keys**: Use deterministic hashing (topic+format+tone for mappings)
9. **Embeddings**: Use `all-MiniLM-L6-v2` (384-dim, fast, good quality)
10. **Output Samples**: Generate at least one example per format for validation

---

## ✅ READY TO BEGIN

**Status**: All prerequisites met, templates provided, orchestrator ready.

**Command to start**:
```bash
python MARATHON_KICKOFF.py --full
```

**Cheetah, you have everything you need to build this system end-to-end and generate comprehensive benchmark insights. Let's see what you can do! 🚀**