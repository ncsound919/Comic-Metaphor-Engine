# 🚀 CHEETAH V3 MARATHON - QUICK REFERENCE CARD

## ONE-LINER TO START
```bash
cd "Build Lab/Book-Writing-Assistant--main/Comic Metaphor Logic" && python MARATHON_KICKOFF.py --full
```

---

## PROJECT AT A GLANCE

**Goal**: Build complete comic book metaphor engine + benchmark it  
**Input**: 4 storyline protocols (Armor Wars, Secret Invasion, etc.)  
**Output**: Searchable metaphor system generating podcast/marketing/dialogue content  
**Benchmark**: 37 scenarios measuring speed, cache, quality, resources  
**Time**: 60-90 minutes  

---

## STATUS CHECKLIST

### ✅ READY (Built by Human)
- [x] schema.py (1,065 lines - all data models)
- [x] __init__.py (module structure)
- [x] MARATHON_KICKOFF.py (orchestrator)
- [x] requirements.txt (dependencies)
- [x] Templates 01-15 (specs)
- [x] Source data (4 protocols)

### 🔨 TO BUILD (Cheetah's Job)
- [ ] engine/ingest.py (434 lines template provided)
- [ ] engine/index.py (FAISS search)
- [ ] engine/metaphor_engine.py (mapping logic)
- [ ] engine/narrative_generator.py (script generation)
- [ ] engine/explainers.py (explanations)
- [ ] engine/codex_adapter.py (scoring wrapper)
- [ ] engine/tools_interface.py (Cheetah integration)
- [ ] benchmarks/scenarios/*.json (3 scenario files)
- [ ] benchmarks/run_benchmark.py (benchmark runner)
- [ ] tests/*.py (4 test files)

---

## BUILD PHASES

| Phase | Time | What Happens | Output |
|-------|------|--------------|--------|
| 0 | 2m | Checks | Dependencies verified |
| 1 | 5m | Ingestion | processed/knowledge_base.json (4 protocols) |
| 2 | 3m | Indexing | processed/faiss_index.bin |
| 3 | 8m | Engine | Mapping + scoring working |
| 4 | 10m | Generation | Sample scripts in output/ |
| 5 | 7m | Integration | Tools wired to Cheetah |
| 6 | 5m | Tests | All passing |
| 7 | 15m | Benchmark | 37 scenarios executed |
| 8 | 3m | Advisor | Recommendations generated |

**Total: ~58 minutes + buffer**

---

## KEY COMMANDS

```bash
# Full marathon
python MARATHON_KICKOFF.py --full

# Individual phase
python MARATHON_KICKOFF.py --phase 1

# Benchmark only (assumes system built)
python MARATHON_KICKOFF.py --benchmark-only

# Tests only
python MARATHON_KICKOFF.py --test-only

# Install deps
pip install -r requirements.txt

# Verify setup
python -c "from engine.schema import Protocol; print('✓ Schema ready')"
```

---

## CRITICAL FILES

| File | Purpose | When to Read |
|------|---------|--------------|
| START_HERE.md | Quick start | First |
| README_CHEETAH_MARATHON.md | Full guide (686 lines) | Before build |
| BUILD_STATUS.md | Component checklist | During build |
| MARATHON_BUILD_SPEC.md | Technical specs (507 lines) | Implementation |
| TEMPLATE_01_ingest.py | Reference code (434 lines) | For patterns |

---

## SUCCESS CRITERIA

### Must Have ✓
- [ ] 4 protocols loaded from "Storylines for metaphor engine"
- [ ] Search returns relevant protocols for queries
- [ ] Mappings generated with codex scores (Trueness, Flow, etc.)
- [ ] Scripts produced for podcast/marketing/dialogue
- [ ] 37 scenarios executed (<5s avg)
- [ ] Cache hit rate >30%
- [ ] All tests passing
- [ ] Zero crashes

### Nice to Have ⭐
- [ ] 90%+ mappings score Trueness ≥0.6
- [ ] Advisor gives 3+ actionable recommendations
- [ ] Sample outputs in output/ directory
- [ ] Marathon report generated

---

## DATA FLOW

```
Storylines file → Ingest → Knowledge Base → Index → Search
                              ↓
                         Metaphor Engine → Mapping
                              ↓
                         Codex Adapter → Scores
                              ↓
                    Narrative Generator → Scripts
                              ↓
                         Tools Interface → Benchmark
                              ↓
                      Cheetah Advisor → Insights
```

---

## THE 4 PROTOCOLS

1. **Armor Wars** (Ownership) - "My IP leaked, now it's everywhere"
2. **Secret Invasion** (Identity) - "Can't trust anyone, deepfake reality"
3. **Days of Future Past** (Control) - "AI optimization killed freedom"
4. **Planet Hulk** (Avoidance) - "Externalized problems return 10x worse"

Each = 4 dimensions (Bio, Tech, Eco, Cosmic) + business vectors

---

## OUTPUTS LOCATION

```
processed/                      ← Phase 1 output
├── knowledge_base.json         (4 protocols)
├── protocols.jsonl
└── embeddings.npy              (4 x 384 vectors)

output/                         ← Samples + reports
├── sample_podcast.md
├── sample_marketing.md
├── sample_dialogue.md
└── marathon_report_*.txt

../../Cheetah-v3-Pro/benchmark_results/  ← Benchmark data
├── comic_metaphor_*.json
└── comic_metaphor_advisor_*.md
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Import error | `cd "Comic Metaphor Logic" && python -c "from engine.schema import Protocol"` |
| Missing packages | `pip install -r requirements.txt --upgrade` |
| Phase failed | `python MARATHON_KICKOFF.py --phase N` (re-run) |
| Tests failing | `pytest tests/test_X.py -v` (detailed output) |
| Cheetah not found | Check `../../Cheetah-v3-Pro/` exists |

---

## BENCHMARK METRICS

**Per Scenario**:
- Latency (ms)
- Cache hits/misses
- CPU usage (avg/peak)
- Memory usage (peak)
- Codex scores (6 metrics)
- TAP score (weighted)
- Output validation (word count, beats)

**Aggregate**:
- Success rate (scenarios passed / total)
- Average latency
- Cache hit rate
- Quality distribution
- Performance bottlenecks
- Optimization opportunities

---

## INTEGRATION POINTS

- **Cheetah v3**: `../../Cheetah-v3-Pro/tools/tool_runs/`
- **Codex Engine**: `./codex_engine.py` (existing)
- **Source Data**: `./Storylines for metaphor engine`
- **TAP Metrics**: `./IHS_*.csv` and `./IHS_*.json`
- **UI Component**: `Metaphor Intelligence Engine` (React)

---

## DEPENDENCIES

Core: pandas, numpy, faiss-cpu, sentence-transformers, scikit-learn  
Testing: pytest, pytest-cov, pytest-mock  
Utils: python-dateutil, tqdm  

Install: `pip install -r requirements.txt`

---

## MARATHON MODES

| Mode | Command | Use Case |
|------|---------|----------|
| Full | `--full` | Complete build + benchmark |
| Phase | `--phase N` | Build one phase |
| Benchmark | `--benchmark-only` | Test existing system |
| Test | `--test-only` | Run tests |

---

## POST-COMPLETION

1. Read: `output/marathon_report_*.txt`
2. Check: `output/sample_*.md` (quality)
3. Analyze: `benchmark_results/comic_metaphor_*.json`
4. Review: `benchmark_results/comic_metaphor_advisor_*.md`
5. Optimize: Apply recommendations
6. Re-run: `--benchmark-only` to measure gains

---

## ONE-PAGE SUMMARY

**You have**: 4 storyline protocols + scoring engine + Cheetah v3 framework  
**Cheetah builds**: Data ingestion → search → mapping → generation → benchmark  
**Result**: Complete metaphor system with 37-scenario performance analysis  
**Time**: ~60-90 minutes  
**Value**: Tests Cheetah's end-to-end system building capability  

---

## START NOW

```bash
cd "Build Lab/Book-Writing-Assistant--main/Comic Metaphor Logic"
python MARATHON_KICKOFF.py --full
```

**Watch the magic happen! ✨**