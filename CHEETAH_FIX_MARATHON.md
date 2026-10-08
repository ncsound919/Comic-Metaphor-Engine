# 🐆 CHEETAH FIX MARATHON - CSL-X COMMAND SEQUENCE

**Mission**: Marathon code all critical fixes to make Comic Metaphor Engine production-ready  
**Method**: Cheetah V3 Pro CSL-X automation  
**Priority**: Critical issues first, then high, medium, low

---

## 🎯 MASTER EXECUTION COMMAND

```csl
!@b5+cmpelv^95>#fix[
  critical~5,
  high~6,
  medium~5,
  polish~4
]>#val[syntax,tests,integration]>#exp[py,json,md]
```

**Translation**: Generate book-length fixes with caching, monitoring, parallel processing, error recovery, logging, validation at 95% quality gate. Fix critical issues (5), high priority (6), medium (5), polish (4). Validate syntax, tests, and integration. Export as Python, JSON, and Markdown.

---

## 🚨 PHASE 1: CRITICAL FIXES (Blocking Issues)

### Fix #1: Protocol Parser for .txt → JSON
**Priority**: CRITICAL  
**Estimated Lines**: 400-500  
**Dependencies**: None

```csl
!@ra+cev^95>#gen[protocol_parser.py]>#val[
  $v/parse_txt_protocol,
  $v/extract_json_blocks,
  $v/validate_dimensions,
  $v/build_knowledge_base
]>#test[unit,integration]
```

**Specifications**:
- File: `engine/protocol_parser.py`
- Parse markdown-formatted protocols from `.txt` files
- Extract: narrative, business_translation, dimensions (D1-D4), vector_entry JSON
- Validate: 4 dimensions present, JSON parseable, required fields exist
- Output: Populated `knowledge_base.json` with 65 protocols
- Error handling: Report line numbers for parsing failures
- Support: cosmic_entities_complete.txt, claremont_xmen_complete.txt, xmen_modern_era_complete.txt

**Key Functions**:
```python
def parse_protocol_file(file_path: Path) -> List[Protocol]
def extract_protocol_section(content: str, start_marker: str) -> Dict
def parse_dimension_block(text: str) -> Dimension
def extract_vector_json(text: str) -> Dict
def validate_protocol(protocol: Protocol) -> List[str]  # Returns errors
def sync_to_knowledge_base(protocols: List[Protocol], kb_path: Path) -> None
```

---

### Fix #2: Schema Update - Flexible Protocol Types
**Priority**: CRITICAL  
**Estimated Lines**: 50-100  
**Dependencies**: None

```csl
!@ms+cev^95>#update[engine/schema.py]>#mod[
  ProtocolType:enum→string,
  +validation_method,
  +protocol_categories
]
```

**Changes Required**:
```python
# BEFORE:
class ProtocolType(Enum):
    ARMOR_WARS = "armor_wars"
    # ... only 9 values

# AFTER:
class ProtocolCategory(Enum):
    COSMIC_ENTITY = "cosmic_entity"
    CLAREMONT_ARC = "claremont_arc"
    MODERN_XMEN = "modern_xmen"
    AVENGERS_COSMIC = "avengers_cosmic"
    CHARACTER_DEEP_DIVE = "character_deep_dive"
    CUSTOM = "custom"

class Protocol:
    protocol_type: str  # Changed from ProtocolType enum
    category: ProtocolCategory
    
    def validate_type(self) -> bool:
        """Validate protocol_type is reasonable"""
        return len(self.protocol_type) > 5 and self.protocol_type.startswith("protocol_")
```

---

### Fix #3: Real Tests for Protocol Parsing
**Priority**: CRITICAL  
**Estimated Lines**: 300-400  
**Dependencies**: Fix #1

```csl
!@ut+cev^95>#gen[tests/test_protocol_parser.py]>#val[
  coverage>85%,
  edge_cases,
  error_conditions
]
```

**Test Coverage**:
```python
def test_parse_single_protocol():
    """Test parsing one complete protocol"""
    
def test_parse_all_dimensions():
    """Test D1, D2, D3, D4 extraction"""
    
def test_extract_json_vector_entry():
    """Test JSON block extraction from markdown"""
    
def test_parse_multiple_protocols_from_file():
    """Test parsing cosmic_entities_complete.txt (23 protocols)"""
    
def test_validation_catches_missing_dimensions():
    """Test validator catches incomplete protocols"""
    
def test_sync_to_knowledge_base():
    """Test updating knowledge_base.json"""
    
def test_error_handling_malformed_protocol():
    """Test graceful handling of parse errors"""
```

---

### Fix #4: VectorDatabaseBuilder Real Implementation
**Priority**: CRITICAL  
**Estimated Lines**: 200-300  
**Dependencies**: Fix #1

```csl
!@ms+cev^95>#update[CHEETAH_MARATHON_ORCHESTRATOR.py]>#mod[
  VectorDatabaseBuilder.load_existing_protocols,
  VectorDatabaseBuilder.add_protocol,
  VectorDatabaseBuilder.build_database,
  +embedding_generation
]
```

**Implementation**:
```python
class VectorDatabaseBuilder:
    def load_existing_protocols(self):
        """Actually parse protocol files"""
        from engine.protocol_parser import parse_protocol_file
        
        protocol_files = [
            OUTPUT_DIR / "cosmic_entities_complete.txt",
            OUTPUT_DIR / "claremont_xmen_complete.txt",
            OUTPUT_DIR / "xmen_modern_era_complete.txt",
        ]
        
        for file_path in protocol_files:
            if file_path.exists():
                protocols = parse_protocol_file(file_path)
                for protocol in protocols:
                    self.add_protocol(protocol.to_dict())
                print(f"  ✓ Loaded {len(protocols)} from {file_path.name}")
    
    def add_protocol(self, protocol_data: Dict):
        """Add with indexing"""
        self.vector_db["protocols"].append(protocol_data)
        # Build indices for fast lookup
        # ...
    
    def build_database(self) -> Dict:
        """Build complete vector database with embeddings"""
        self.load_existing_protocols()
        self._generate_embeddings()
        self._build_cross_references()
        return self.vector_db
```

---

### Fix #5: Progress Tracker Initialization
**Priority**: CRITICAL  
**Estimated Lines**: 50-100  
**Dependencies**: None

```csl
!@ms+cev^95>#update[CHEETAH_MARATHON_ORCHESTRATOR.py]>#mod[
  MarathonProgressTracker._load_progress,
  +scan_existing_files,
  +initialize_from_config
]
```

**Fix**:
```python
def _load_progress(self) -> Dict:
    """Load existing progress or initialize with actual state"""
    if self.progress_file.exists():
        with open(self.progress_file, "r") as f:
            return json.load(f)
    
    # Initialize with known completions from MARATHON_CONFIG
    completed_count = sum(MARATHON_CONFIG["completed"].values())
    
    # Or scan files to count protocols
    actual_count = self._count_existing_protocols()
    
    return {
        "started_at": datetime.now().isoformat(),
        "phases": self._initialize_phases(),
        "protocols_completed": self._scan_completed_protocol_ids(),
        "total_protocols": actual_count,
        "total_dimensions_mapped": actual_count * 4,
        "status": "initialized",
    }

def _count_existing_protocols(self) -> int:
    """Scan files to count actual protocols"""
    count = 0
    for file in OUTPUT_DIR.glob("*.txt"):
        if file.name != "sample_comic.txt":
            # Quick count of "protocol_" occurrences
            content = file.read_text()
            count += content.count('"id": "protocol_')
    return count
```

---

## 🔥 PHASE 2: HIGH PRIORITY FIXES

### Fix #6: Test Suite Completion
**Priority**: HIGH  
**Estimated Lines**: 600-800  
**Dependencies**: Fix #1, #2

```csl
!@ut+cev^95>#gen[
  tests/test_schema.py,
  tests/test_orchestrator.py,
  tests/test_integration_full.py
]>#val[coverage>80%]
```

**test_schema.py** (200 lines):
```python
def test_dimension_creation_and_validation()
def test_protocol_to_dict_from_dict_roundtrip()
def test_business_vector_serialization()
def test_knowledge_base_save_load()
def test_protocol_category_validation()
```

**test_orchestrator.py** (200 lines):
```python
def test_progress_tracker_persistence()
def test_phase_execution_tracking()
def test_vector_database_builder()
def test_cslx_command_generation()
def test_marathon_completion_calculation()
```

**test_integration_full.py** (200 lines):
```python
def test_full_pipeline_txt_to_knowledge_base()
def test_end_to_end_protocol_retrieval()
def test_marathon_orchestrator_integration()
def test_codex_engine_integration()
```

---

### Fix #7: Error Handling Throughout
**Priority**: HIGH  
**Estimated Lines**: 150-200  
**Dependencies**: None

```csl
!@ms+ev^95>#update[
  CHEETAH_MARATHON_ORCHESTRATOR.py,
  engine/protocol_parser.py
]>#add[
  error_handling,
  logging,
  validation
]
```

**Pattern to Apply**:
```python
import logging
logger = logging.getLogger(__name__)

def load_existing_protocols(self):
    """Load protocols with error handling"""
    try:
        for file_path in protocol_files:
            try:
                if not file_path.exists():
                    logger.warning(f"Protocol file not found: {file_path}")
                    continue
                
                protocols = parse_protocol_file(file_path)
                logger.info(f"Loaded {len(protocols)} protocols from {file_path.name}")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error in {file_path}: {e}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                
    except Exception as e:
        logger.critical(f"Fatal error loading protocols: {e}")
        raise
```

---

### Fix #8: Protocol Validation System
**Priority**: HIGH  
**Estimated Lines**: 300-400  
**Dependencies**: Fix #1

```csl
!@ra+cev^95>#gen[engine/protocol_validator.py]>#val[
  json_validation,
  dimension_completeness,
  metric_presence,
  id_uniqueness
]
```

**Validator Implementation**:
```python
class ProtocolValidator:
    """Validates protocol format and completeness"""
    
    def validate_protocol(self, protocol: Protocol) -> ValidationResult:
        """Comprehensive protocol validation"""
        errors = []
        warnings = []
        
        # Check ID format
        if not protocol.id.startswith("protocol_"):
            errors.append(f"Invalid ID format: {protocol.id}")
        
        # Check dimensions
        if len(protocol.dimensions) != 4:
            errors.append(f"Expected 4 dimensions, found {len(protocol.dimensions)}")
        
        dimension_types = {d.id for d in protocol.dimensions}
        expected = {DimensionType.D1_BIO, DimensionType.D2_TECH, 
                   DimensionType.D3_ECO, DimensionType.D4_COSMIC}
        
        if dimension_types != expected:
            missing = expected - dimension_types
            errors.append(f"Missing dimensions: {missing}")
        
        # Check each dimension has metric
        for dim in protocol.dimensions:
            if not dim.metric or len(dim.metric) < 10:
                warnings.append(f"{dim.id} missing or short metric")
        
        # Validate JSON vector entry
        try:
            json.dumps(protocol.vector_entry)
        except Exception as e:
            errors.append(f"Invalid vector_entry JSON: {e}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_file(self, file_path: Path) -> FileValidationResult:
        """Validate entire protocol file"""
        protocols = parse_protocol_file(file_path)
        results = [self.validate_protocol(p) for p in protocols]
        
        # Check for duplicate IDs
        ids = [p.id for p in protocols]
        duplicates = [id for id in ids if ids.count(id) > 1]
        
        return FileValidationResult(
            file=file_path,
            protocol_count=len(protocols),
            results=results,
            duplicates=duplicates
        )
```

---

### Fix #9: Orchestrator Real Content Generation
**Priority**: HIGH  
**Estimated Lines**: 400-500  
**Dependencies**: Fix #1

```csl
!@ms+cev^95>#update[CHEETAH_MARATHON_ORCHESTRATOR.py]>#mod[
  execute_phase_avengers,
  execute_phase_characters,
  +template_rendering,
  +file_writing
]
```

**Implementation Options**:
```python
# Option A: Template-based generation
def execute_phase_avengers(self):
    """Generate Avengers protocols from templates"""
    from engine.protocol_generator import ProtocolGenerator
    
    generator = ProtocolGenerator(templates_dir="templates/")
    output_file = OUTPUT_DIR / "avengers_cosmic_complete.txt"
    
    with open(output_file, 'w') as f:
        f.write("# AVENGERS COSMIC SAGAS - COMPLETE METAPHOR DATABASE\n\n")
        
        for storyline_spec in AVENGERS_STORYLINES:
            protocol = generator.generate_from_spec(storyline_spec)
            f.write(protocol.to_markdown())
            f.write("\n\n---\n\n")
            
            self.tracker.complete_protocol("avengers_cosmic", protocol.id)
    
    logger.info(f"Generated {len(AVENGERS_STORYLINES)} protocols to {output_file}")

# Option B: Call Cheetah via subprocess
def execute_phase_avengers_with_cheetah(self):
    """Execute using Cheetah CSL-X"""
    import subprocess
    
    cslx_cmd = CSLX_COMMANDS["avengers"]
    cheetah_path = CHEETAH_ROOT / "cheetah_cli.py"
    
    result = subprocess.run(
        ["python", str(cheetah_path), "--cslx", cslx_cmd],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("Cheetah generation successful")
    else:
        logger.error(f"Cheetah error: {result.stderr}")
```

---

### Fix #10: Documentation Consolidation
**Priority**: HIGH  
**Estimated Lines**: 200-300  
**Dependencies**: None

```csl
!@dg+cv^90>#consolidate[
  MISSION_CONTROL.md→dashboard_only,
  MARATHON_STATUS_REPORT.md→archive,
  MARATHON_QUICK_START.md→README_EXTENDED.md
]>#create[DEVELOPER_GUIDE.md]
```

**New Structure**:
- `README.md` - 5-minute overview, quick start
- `DEVELOPER_GUIDE.md` - Technical architecture, API docs
- `MISSION_CONTROL.md` - Status dashboard only (dynamic)
- Archive old duplicate docs

---

### Fix #11: Cheetah Integration Documentation
**Priority**: HIGH  
**Estimated Lines**: 100-150  
**Dependencies**: None

```csl
!@dg+cv^90>#create[CHEETAH_INTEGRATION.md]>#document[
  cslx_commands,
  execution_modes,
  manual_vs_automated,
  troubleshooting
]
```

**Document**:
- How CSL-X commands work
- Manual copy-paste vs subprocess execution
- Required Cheetah V3 Pro setup
- Fallback modes if Cheetah unavailable

---

## ⚠️ PHASE 3: MEDIUM PRIORITY FIXES

### Fix #12: Logging System
**Priority**: MEDIUM  
**Estimated Lines**: 100-150

```csl
!@ms+cv^90>#add[logging_config]>#update[
  CHEETAH_MARATHON_ORCHESTRATOR.py,
  engine/protocol_parser.py,
  engine/ingest.py
]
```

**Configuration**:
```python
# logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file="marathon.log"):
    """Configure logging for marathon system"""
    
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
```

---

### Fix #13: Path Cross-Platform Compatibility
**Priority**: MEDIUM  
**Estimated Lines**: 50-100

```csl
!@ms+cv^90>#audit[path_usage]>#fix[
  use_pathlib_consistently,
  remove_hardcoded_separators
]
```

**Changes**:
```python
# BEFORE:
path = "comic_books\\file.txt"  # Windows-only
path = root + "/" + filename    # String concatenation

# AFTER:
from pathlib import Path
path = Path("comic_books") / "file.txt"  # Cross-platform
path = root / filename  # Pathlib operation
```

---

### Fix #14: Codex Engine Integration Verification
**Priority**: MEDIUM  
**Estimated Lines**: 200-300

```csl
!@ms+cev^90>#verify[engine/codex_adapter.py]>#test[
  protocol_to_codex_input,
  codex_scoring,
  integration
]
```

**Verification Test**:
```python
def test_codex_adapter_with_protocol():
    """Test that codex_adapter works with our protocols"""
    from engine.codex_adapter import CodexAdapter
    from engine.protocol_parser import parse_protocol_file
    
    protocols = parse_protocol_file("cosmic_entities_complete.txt")
    adapter = CodexAdapter()
    
    for protocol in protocols[:5]:  # Test first 5
        codex_input = adapter.protocol_to_codex_input(protocol)
        report, audit = compute_report(codex_input)
        
        assert audit["scores"]["Trueness"] is not None
        assert "GO" in audit["decision"] or "NO-GO" in audit["decision"]
```

---

### Fix #15: Magic Numbers Documentation
**Priority**: MEDIUM  
**Estimated Lines**: 50-100

```csl
!@dg+cv^90>#document[magic_numbers]>#add[
  CONSTANTS.py,
  inline_comments
]
```

**New File**:
```python
# CONSTANTS.py
"""
Marathon Configuration Constants

Target Protocol Counts:
- Cosmic Entities: 23 (Watchers, Galactus, Thanos, etc.)
- Claremont X-Men: 20 (Dark Phoenix, Days Future Past, etc.)
- Modern X-Men: 22 (House of M, Krakoa, etc.)
- Avengers Cosmic: 20 (Kree-Skrull War, Korvac, etc.)
- Character Deep Dives: 18 (Thanos philosophy, etc.)
TOTAL: 103 protocols
"""

COSMIC_ENTITY_TARGET = 23
CLAREMONT_TARGET = 20
MODERN_XMEN_TARGET = 22
AVENGERS_COSMIC_TARGET = 20
CHARACTER_DEEP_DIVE_TARGET = 18

TOTAL_TARGET = (
    COSMIC_ENTITY_TARGET +
    CLAREMONT_TARGET +
    MODERN_XMEN_TARGET +
    AVENGERS_COSMIC_TARGET +
    CHARACTER_DEEP_DIVE_TARGET
)

assert TOTAL_TARGET == 103, "Target count mismatch!"
```

---

## 📝 PHASE 4: POLISH & OPTIMIZATION

### Fix #16: Import Cleanup
**Priority**: LOW  
**Estimated Lines**: 10-20

```csl
!@ms+cv^85>#cleanup[unused_imports]>#format[black,isort]
```

---

### Fix #17: Type Hints Completeness
**Priority**: LOW  
**Estimated Lines**: 100-150

```csl
!@ms+cv^85>#add[type_hints]>#validate[mypy]
```

---

### Fix #18: Docstring Completeness
**Priority**: LOW  
**Estimated Lines**: 200-300

```csl
!@dg+cv^85>#audit[docstrings]>#add[missing_docstrings]
```

---

### Fix #19: Performance Profiling
**Priority**: LOW  
**Estimated Lines**: 100-150

```csl
!@pt+cv^85>#profile[
  protocol_parsing_speed,
  embedding_generation_time,
  database_build_time
]>#optimize[bottlenecks]
```

---

## 🚀 EXECUTION SEQUENCE

### Sequential Execution (Recommended)
```csl
# Day 1: Critical Blockers
!&#fix[critical~5]>#phase[1]
?p  # Check progress
!$v/test[phase1]  # Validate

# Day 2: High Priority  
!&#fix[high~6]>#phase[2]
?p
!$v/test[phase2]

# Day 3: Medium Priority
!&#fix[medium~5]>#phase[3]
?p
!$v/test[phase3]

# Day 4: Polish
!&#fix[polish~4]>#phase[4]
?p
!$v/test[all]
```

### Parallel Execution (Faster, Riskier)
```csl
!&[
  #fix[critical~5],
  #fix[high~6],
  #fix[medium~5]
]>#val[all]>#exp[py,json,md]
```

---

## ✅ VALIDATION GATES

After each phase:

```csl
# Syntax validation
$v/syntax~all

# Test coverage
$v/coverage>80%

# Integration check
$v/integration[
  txt→json,
  json→vector_db,
  vector_db→search
]

# Performance check
$v/performance[
  parse_time<5s/file,
  search_latency<100ms
]
```

---

## 📊 SUCCESS METRICS

```
BEFORE FIX MARATHON:
- knowledge_base.json: 6 protocols, 0 dimensions populated
- Tests: 4 placeholder stubs
- Error handling: None
- Logging: print() statements only
- Documentation: 4 files with duplication
- Integration: Disconnected components

AFTER FIX MARATHON:
- knowledge_base.json: 65+ protocols, all dimensions populated
- Tests: 15+ real tests, >80% coverage
- Error handling: try/except throughout, graceful failures
- Logging: Proper logging with levels and files
- Documentation: Consolidated, single source of truth
- Integration: Fully connected pipeline
```

---

## 🎯 ESTIMATED TIMELINE

**With Cheetah Automation**:
- Phase 1 (Critical): 2-3 hours
- Phase 2 (High): 2-3 hours
- Phase 3 (Medium): 1-2 hours
- Phase 4 (Polish): 1 hour
**Total**: 6-9 hours

**Manual Coding**:
- Phase 1: 1-2 days
- Phase 2: 1-2 days
- Phase 3: 1 day
- Phase 4: 0.5 days
**Total**: 3.5-5.5 days

---

**READY TO EXECUTE FIX MARATHON WITH CHEETAH** 🐆⚡

```
!@b5+cmpelv^95>#fix[critical~5,high~6,medium~5,polish~4]>#val[all]>#exp[py,json,md]
```
