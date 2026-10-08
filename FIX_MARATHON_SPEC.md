# CHEETAH MARATHON - FIX SPECIFICATION

**Mission**: Fix all 6 minor issues identified in validation  
**Approach**: Automated Cheetah marathon build  
**Duration**: Estimated 15-20 minutes  
**Priority**: Critical path fixes  

---

## FIX 1: FAISS Index Persistence

**Issue**: Index built in-memory but not saved to disk  
**Impact**: Low - rebuilds on startup  
**File**: `engine/index.py`  

**Fix Required**:
```python
# In build_index() function, after creating FAISS index, add:
def build_index(processed_dir: str = "processed", force_rebuild: bool = False):
    # ... existing code ...
    
    # Build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    # NEW: Save index to disk
    index_path = Path(processed_dir) / "faiss_index.bin"
    faiss.write_index(index, str(index_path))
    print(f"✓ Saved FAISS index to {index_path}")
    
    return index
```

**Validation**:
- File `processed/faiss_index.bin` should exist after build
- File size should be >0 bytes
- Can load index with `faiss.read_index()`

---

## FIX 2: Knowledge Base Protocol Access

**Issue**: Protocols accessed as dict, expected as list  
**Impact**: Low - API inconsistency  
**File**: `engine/schema.py`  

**Fix Required**:
```python
class KnowledgeBase:
    """Knowledge base with protocol collection"""
    
    def __init__(self):
        self.protocols: Dict[str, Protocol] = {}
        self.universes: Dict[str, Universe] = {}
        self._protocol_list = None  # Cache for list access
    
    def __getitem__(self, key):
        """Support both dict and list access"""
        if isinstance(key, str):
            return self.protocols[key]
        elif isinstance(key, int):
            return list(self.protocols.values())[key]
        elif isinstance(key, slice):
            return list(self.protocols.values())[key]
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
    
    def __len__(self):
        return len(self.protocols)
    
    def __iter__(self):
        return iter(self.protocols.values())
```

**Validation**:
- `kb.protocols[:3]` should work
- `kb.protocols[0]` should return first protocol
- `kb.protocols['protocol_id']` should still work

---

## FIX 3: NarrativeGenerator API Signature

**Issue**: Init expects no args, tests pass "processed"  
**Impact**: Medium - API mismatch  
**File**: `engine/narrative_generator.py`  

**Fix Required**:
```python
class NarrativeGenerator:
    """Generate narrative content from metaphor mappings"""
    
    def __init__(self, processed_dir: str = "processed"):
        """Initialize with processed data directory
        
        Args:
            processed_dir: Directory containing knowledge_base.json
        """
        self.processed_dir = Path(processed_dir)
        
        # Load knowledge base
        kb_path = self.processed_dir / "knowledge_base.json"
        self.knowledge_base = KnowledgeBase.load(str(kb_path))
        
        # Initialize templates
        self._load_templates()
    
    def _load_templates(self):
        """Load narrative templates"""
        self.templates = {
            'podcast': self._get_podcast_template(),
            'marketing': self._get_marketing_template(),
            'dialogue': self._get_dialogue_template()
        }
```

**Validation**:
- `NarrativeGenerator()` works (defaults to "processed")
- `NarrativeGenerator("processed")` works
- Has `knowledge_base` attribute after init

---

## FIX 4: MetaphorEngine API Signature

**Issue**: Init signature differs from test expectations  
**Impact**: Medium - API mismatch  
**File**: `engine/metaphor_engine.py`  

**Fix Required**:
```python
class MetaphorEngine:
    """Maps topics to comic book metaphors"""
    
    def __init__(self, processed_dir: str = "processed"):
        """Initialize metaphor engine
        
        Args:
            processed_dir: Directory containing processed data
        """
        self.processed_dir = Path(processed_dir)
        
        # Load knowledge base
        kb_path = self.processed_dir / "knowledge_base.json"
        self.knowledge_base = KnowledgeBase.load(str(kb_path))
        
        # Initialize search index
        self.index = MetaphorIndex(str(self.processed_dir))
        
        # Load codex adapter for scoring
        self.codex = CodexAdapter()
    
    def generate(self, topic: str, top_k: int = 3) -> MetaphorMapping:
        """Generate metaphor mapping for topic
        
        Args:
            topic: Topic to find metaphor for
            top_k: Number of candidate protocols to consider
            
        Returns:
            Best metaphor mapping
        """
        # Search for relevant protocols
        candidates = self.index.search(topic, top_k=top_k)
        
        # Score each candidate
        best_mapping = None
        best_score = -1
        
        for protocol_id, score in candidates:
            protocol = self.knowledge_base.protocols[protocol_id]
            
            # Generate mapping
            mapping = MetaphorMapping(
                mapping_id=self._generate_id(),
                topic=topic,
                protocol_id=protocol_id,
                protocol_name=protocol.name,
                relevance_score=score
            )
            
            # Score with codex
            trueness = self.codex.score(mapping)
            mapping.trueness_score = trueness
            
            if trueness > best_score:
                best_score = trueness
                best_mapping = mapping
        
        return best_mapping
```

**Validation**:
- `MetaphorEngine()` works
- `MetaphorEngine("processed")` works
- Has `generate()` method
- Has `knowledge_base` and `index` attributes

---

## FIX 5: Benchmark Path Resolution

**Issue**: Benchmark looks for Cheetah v3 in wrong location  
**Impact**: Medium - benchmarks don't run  
**File**: `benchmarks/run_benchmark.py`  

**Fix Required**:
```python
class BenchmarkRunner:
    """Run comprehensive benchmark suite"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        
        # FIXED: Point to correct Cheetah v3 Pro location
        self.cheetah_root = (
            self.project_root.parent.parent.parent.parent / "Overlay Cheetah v3 Pro"
        )
        
        # Create results directory
        self.results_dir = self.cheetah_root / "benchmark_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load processed data
        self.processed_dir = self.project_root / "processed"
        self.engine = MetaphorEngine(str(self.processed_dir))
```

**Validation**:
- Results directory created successfully
- Can write results files
- Benchmark suite executes without path errors

---

## FIX 6: Test Implementations

**Issue**: Test files have placeholder implementations  
**Impact**: Low - functionality works, just not formally tested  
**Files**: 
- `tests/test_ingest.py`
- `tests/test_index.py`
- `tests/test_metaphor_engine.py`
- `tests/test_integration.py`

**Fix Required - test_ingest.py**:
```python
import pytest
from pathlib import Path
from engine.schema import KnowledgeBase
from engine.ingest import parse_storylines_file, build_knowledge_base


def test_knowledge_base_loads():
    """Test that knowledge base loads successfully"""
    kb = KnowledgeBase.load("processed/knowledge_base.json")
    assert kb is not None
    assert len(kb.protocols) > 0


def test_knowledge_base_has_protocols():
    """Test knowledge base contains expected protocols"""
    kb = KnowledgeBase.load("processed/knowledge_base.json")
    assert len(kb.protocols) >= 6
    
    # Check protocol structure
    for protocol_id, protocol in list(kb.protocols.items())[:3]:
        assert protocol.name
        assert protocol.core_metaphor
        assert protocol.d1_bio
        assert protocol.d2_tech
        assert protocol.d3_eco
        assert protocol.d4_cosmic


def test_embeddings_exist():
    """Test that embeddings were generated"""
    embeddings_path = Path("processed/embeddings.npy")
    assert embeddings_path.exists()
    
    import numpy as np
    embeddings = np.load(embeddings_path)
    assert embeddings.shape[1] == 384  # 384-dim sentence-transformers


def test_metadata_complete():
    """Test that metadata was generated"""
    import json
    metadata_path = Path("processed/metadata.json")
    assert metadata_path.exists()
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'total_protocols' in metadata
    assert metadata['total_protocols'] >= 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Fix Required - test_index.py**:
```python
import pytest
from engine.index import MetaphorIndex


def test_index_loads():
    """Test that index loads successfully"""
    index = MetaphorIndex("processed")
    assert index is not None


def test_index_has_vectors():
    """Test index contains vectors"""
    index = MetaphorIndex("processed")
    assert index.index is not None
    assert index.index.ntotal > 0


def test_search_works():
    """Test that search returns results"""
    index = MetaphorIndex("processed")
    results = index.search("burnout", top_k=3)
    
    assert len(results) > 0
    assert all(len(r) == 2 for r in results)  # (id, score) tuples


def test_search_returns_relevant_results():
    """Test that search returns relevant protocols"""
    index = MetaphorIndex("processed")
    results = index.search("technical debt", top_k=3)
    
    # Should return some results
    assert len(results) > 0
    
    # Scores should be reasonable
    for protocol_id, score in results:
        assert score >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Fix Required - test_metaphor_engine.py**:
```python
import pytest
from engine.metaphor_engine import MetaphorEngine


def test_engine_loads():
    """Test that engine loads successfully"""
    engine = MetaphorEngine("processed")
    assert engine is not None


def test_engine_has_knowledge_base():
    """Test engine loaded knowledge base"""
    engine = MetaphorEngine("processed")
    assert engine.knowledge_base is not None
    assert len(engine.knowledge_base.protocols) > 0


def test_engine_generates_mappings():
    """Test engine can generate mappings"""
    engine = MetaphorEngine("processed")
    
    if hasattr(engine, 'generate'):
        mapping = engine.generate("startup burnout")
        
        assert mapping is not None
        assert hasattr(mapping, 'topic')
        assert hasattr(mapping, 'protocol_id')
        assert mapping.topic == "startup burnout"
    else:
        pytest.skip("Engine doesn't have generate method yet")


def test_engine_scores_mappings():
    """Test engine scores mappings correctly"""
    engine = MetaphorEngine("processed")
    
    if hasattr(engine, 'generate'):
        mapping = engine.generate("technical debt")
        
        assert hasattr(mapping, 'relevance_score')
        assert 0 <= mapping.relevance_score <= 1
    else:
        pytest.skip("Engine doesn't have generate method yet")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Fix Required - test_integration.py**:
```python
import pytest
from engine.schema import KnowledgeBase
from engine.index import MetaphorIndex
from engine.metaphor_engine import MetaphorEngine
from engine.narrative_generator import NarrativeGenerator


def test_end_to_end_pipeline():
    """Test complete pipeline from query to narrative"""
    # Load knowledge base
    kb = KnowledgeBase.load("processed/knowledge_base.json")
    assert len(kb.protocols) > 0
    
    # Initialize engine
    engine = MetaphorEngine("processed")
    assert engine.knowledge_base is not None
    
    # Generate mapping (if available)
    if hasattr(engine, 'generate'):
        mapping = engine.generate("startup scaling")
        assert mapping is not None


def test_all_modules_import():
    """Test that all modules can be imported"""
    from engine import schema
    from engine import ingest
    from engine import index
    from engine import metaphor_engine
    from engine import narrative_generator
    from engine import explainers
    from engine import tools_interface
    from engine import codex_adapter
    
    assert True


def test_knowledge_base_to_search():
    """Test knowledge base to search pipeline"""
    kb = KnowledgeBase.load("processed/knowledge_base.json")
    index = MetaphorIndex("processed")
    
    # Search should return protocol IDs from knowledge base
    results = index.search("burnout", top_k=3)
    
    for protocol_id, score in results:
        # Protocol should exist in knowledge base
        assert protocol_id in kb.protocols


def test_search_to_mapping():
    """Test search to mapping pipeline"""
    engine = MetaphorEngine("processed")
    
    # Engine should be able to use search results
    if hasattr(engine, 'generate'):
        mapping = engine.generate("leadership crisis")
        assert mapping.protocol_id
        assert mapping.protocol_id in engine.knowledge_base.protocols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Validation**:
- All test files run without errors
- 15+ tests pass
- Test coverage improves to 80%+

---

## CHEETAH MARATHON EXECUTION PLAN

### Phase 1: Schema & Data Fixes (5 min)
- Fix FAISS index persistence
- Fix KnowledgeBase protocol access
- Validate data structures

### Phase 2: API Signature Fixes (5 min)
- Fix NarrativeGenerator.__init__
- Fix MetaphorEngine.__init__
- Add generate() method
- Validate APIs

### Phase 3: Path & Integration Fixes (3 min)
- Fix benchmark path resolution
- Create results directory
- Validate paths

### Phase 4: Test Implementation (7 min)
- Implement test_ingest.py (4 tests)
- Implement test_index.py (4 tests)
- Implement test_metaphor_engine.py (4 tests)
- Implement test_integration.py (4 tests)

### Total: ~20 minutes

---

## SUCCESS CRITERIA

After fixes:
- [ ] FAISS index persists to disk
- [ ] Knowledge base supports list/dict access
- [ ] NarrativeGenerator accepts processed_dir arg
- [ ] MetaphorEngine accepts processed_dir arg
- [ ] MetaphorEngine has generate() method
- [ ] Benchmark path resolves correctly
- [ ] All 4 test files have real implementations
- [ ] 16+ tests pass (up from 4)
- [ ] Validation score: 20/20 (up from 14/20)
- [ ] All modules have consistent APIs

---

## EXECUTION COMMAND

```bash
# Run Cheetah marathon with fix specification
python MARATHON_KICKOFF.py --phase 1 --fix-mode

# Or manually apply fixes and re-run validation
python validate_system.py
```

---

## EXPECTED OUTCOME

```
BEFORE FIXES:
- Tests Passing: 14/20 (70%)
- Issues: 6 minor
- Status: Operational

AFTER FIXES:
- Tests Passing: 20/20 (100%)
- Issues: 0
- Status: Production Ready ✅
```

---

**Ready for Cheetah to marathon these fixes!** 🐆⚡