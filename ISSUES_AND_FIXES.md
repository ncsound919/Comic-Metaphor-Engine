# 🔧 COMIC METAPHOR ENGINE - ISSUES & FIXES

**Audit Date**: January 14, 2026  
**Auditor Role**: Senior Developer Review  
**Scope**: Full system audit for production readiness

---

## 🚨 CRITICAL ISSUES

### Issue #1: Knowledge Base Not Synced with Content Files
**Severity**: CRITICAL  
**Location**: `processed/knowledge_base.json` vs `comic_books/*.txt`

**Problem**:
The `knowledge_base.json` contains only 6 protocols with **empty dimensions**, while we've created 65 fully-detailed protocols in the `.txt` files. The two systems are completely disconnected.

```json
// Current state in knowledge_base.json
"protocol_armor_wars": {
  "dimensions": [],        // EMPTY!
  "business_logic": "",    // EMPTY!
  "application": "",       // EMPTY!
  "vector_entry": {}       // EMPTY!
}
```

**Fix Required**:
1. Create a parser to extract structured data from `.txt` files
2. Populate `dimensions` array with actual D1-D4 data
3. Update `CHEETAH_MARATHON_ORCHESTRATOR.py` to run parsing after generation
4. Add validation to ensure knowledge_base stays in sync

**Files to Modify**:
- `engine/ingest.py` - Add new parsing method for our `.txt` format
- `CHEETAH_MARATHON_ORCHESTRATOR.py` - Integrate with ingest pipeline
- `processed/knowledge_base.json` - Will be regenerated

---

### Issue #2: Schema Mismatch - ProtocolType Enum Too Limited
**Severity**: HIGH  
**Location**: `engine/schema.py` lines 91-102

**Problem**:
The `ProtocolType` enum only has 9 values, but we have 65+ different protocols. Most will fail to parse or default to `CUSTOM`.

```python
class ProtocolType(Enum):
    ARMOR_WARS = "armor_wars"
    SECRET_INVASION = "secret_invasion"
    DAYS_OF_FUTURE_PAST = "days_of_future_past"
    PLANET_HULK = "planet_hulk"
    INFINITY_GAUNTLET = "infinity_gauntlet"
    CIVIL_WAR = "civil_war"
    KRAKOA = "krakoa"
    DAMAGE_CONTROL = "damage_control"
    CUSTOM = "custom"  # Everything else falls here
```

**Fix Required**:
Option A: Add all protocol types to enum (tedious, 100+ entries)
Option B: Change to string-based typing with validation (recommended)

```python
# Recommended fix - use string + validation
class Protocol:
    protocol_type: str  # Changed from ProtocolType enum
    
    VALID_TYPES = {"cosmic_entity", "claremont_arc", "modern_xmen", 
                   "avengers_cosmic", "character_deep_dive", "custom"}
    
    def validate_type(self) -> bool:
        return self.protocol_type in self.VALID_TYPES or self.protocol_type == "custom"
```

---

### Issue #3: Test Files Are Empty Stubs
**Severity**: HIGH  
**Location**: `tests/*.py`

**Problem**:
All test files contain only placeholder tests:
```python
def test_placeholder():
    """Placeholder test for test_ingest.py"""
    assert True
```

No actual testing of:
- Protocol parsing
- Dimension extraction
- Vector database building
- Schema validation
- Integration with codex_engine

**Fix Required**:
Create real tests for:
1. `test_ingest.py` - Test parsing of .txt protocol files
2. `test_schema.py` - Test Protocol/Dimension data models
3. `test_orchestrator.py` - Test marathon automation
4. `test_integration.py` - End-to-end pipeline tests

---

### Issue #4: Orchestrator Generates Stubs, Not Real Content
**Severity**: HIGH  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py` lines 454-519

**Problem**:
The `execute_phase_avengers()` and `execute_phase_characters()` methods only simulate content generation with hardcoded stub lists:

```python
# Current implementation - just stubs!
example_protocols = [
    "protocol_kree_skrull_war",
    "protocol_korvac_saga",
    # ...
]
for i, protocol_id in enumerate(example_protocols, 1):
    print(f"  [{i}/{len(example_protocols)}] Generating {protocol_id}...")
    time.sleep(0.1)  # Fake delay!
    self.tracker.complete_protocol(phase_name, protocol_id)
```

**Fix Required**:
1. Integrate with actual content generation (templates or LLM calls)
2. Or: Add file writing to output actual protocol content
3. Connect to Cheetah V3 Pro for CSL-X command execution
4. Add validation that files were actually created

---

### Issue #5: VectorDatabaseBuilder Doesn't Parse Existing Files
**Severity**: HIGH  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py` lines 388-439

**Problem**:
The `VectorDatabaseBuilder.load_existing_protocols()` just checks if files exist but never parses them:

```python
def load_existing_protocols(self):
    """Load all existing protocol files"""
    protocol_files = [...]
    for file_path in protocol_files:
        if file_path.exists():
            print(f"  ✓ Found {file_path.name}")
            # IN REAL IMPLEMENTATION, WOULD PARSE THE FILES
            # FOR NOW, WE TRACK THAT THEY EXIST
```

**Fix Required**:
Implement actual parsing:
1. Read `.txt` files
2. Extract JSON blocks from vector entries
3. Parse dimensions
4. Build searchable index
5. Generate embeddings for semantic search

---

## ⚠️ MEDIUM ISSUES

### Issue #6: Unused Import - `List` and `Optional` from typing
**Severity**: LOW  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py` line 24

```python
from typing import Dict, List, Optional  # List and Optional never used
```

**Fix**: Remove unused imports or use them.

---

### Issue #7: Path Configuration Hardcoded for Windows
**Severity**: MEDIUM  
**Location**: Multiple files

**Problem**:
Paths use backslashes in some places, forward slashes in others. Cross-platform issues possible.

**Fix**: 
Consistently use `pathlib.Path` (which is already imported) for all path operations.

---

### Issue #8: No Error Handling for Missing Files
**Severity**: MEDIUM  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py`

**Problem**:
No try/except around file operations. Will crash if files are missing.

**Fix**:
```python
def load_existing_protocols(self):
    try:
        for file_path in protocol_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._parse_protocols(content)
    except FileNotFoundError as e:
        print(f"Warning: Protocol file not found: {e}")
    except Exception as e:
        print(f"Error loading protocols: {e}")
```

---

### Issue #9: Cheetah Integration Is Placeholder Only
**Severity**: MEDIUM  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py`, CSL-X commands

**Problem**:
The CSL-X commands are defined but never actually sent to Cheetah:
```python
CSLX_COMMANDS = {
    "avengers": "!@b5+cmpelv^90>#gen[...]",
    # These are never executed!
}
```

**Fix**:
Either:
1. Add actual Cheetah integration via subprocess or API
2. Or document that CSL-X is for manual use with Cheetah
3. Add `--cheetah-execute` flag for real integration

---

### Issue #10: Progress Tracker Starts at 0, Ignores Completed Work
**Severity**: MEDIUM  
**Location**: `CHEETAH_MARATHON_ORCHESTRATOR.py` lines 110-122

**Problem**:
When loading progress, existing completed protocols (65) are not counted:

```python
def _load_progress(self) -> Dict:
    if self.progress_file.exists():
        with open(self.progress_file, "r") as f:
            return json.load(f)
    return {
        "total_protocols": 0,  # Should be 65!
        # ...
    }
```

**Fix**:
Initialize with actual completed count from MARATHON_CONFIG or scan files:
```python
def _load_progress(self) -> Dict:
    if self.progress_file.exists():
        return json.load(...)
    
    # Initialize with known completions
    return {
        "total_protocols": sum(MARATHON_CONFIG["completed"].values()),  # 65
        # ...
    }
```

---

### Issue #11: No Validation of Protocol Format in .txt Files
**Severity**: MEDIUM  
**Location**: Content files have no format validation

**Problem**:
The `.txt` files use a custom format but nothing validates:
- JSON blocks are valid JSON
- All 4 dimensions are present
- Required fields exist
- Protocol IDs are unique

**Fix**:
Add validation script that:
1. Parses each protocol section
2. Validates JSON blocks
3. Checks dimension completeness
4. Reports errors with line numbers

---

## 📝 LOW PRIORITY ISSUES

### Issue #12: Duplicate Information Across Documentation Files
**Severity**: LOW  
**Location**: `MISSION_CONTROL.md`, `MARATHON_STATUS_REPORT.md`, `MARATHON_QUICK_START.md`

**Problem**:
Same information repeated in multiple places. Maintenance burden.

**Fix**:
Consider consolidating into:
- `README.md` - Quick overview
- `DEVELOPER_GUIDE.md` - Technical details
- Keep `MISSION_CONTROL.md` as dashboard only

---

### Issue #13: Magic Numbers in Code
**Severity**: LOW  
**Location**: Various

```python
target_count = len(AVENGERS_STORYLINES)  # OK
# But also:
"total_target": 103,  # Why 103? Document it
```

**Fix**:
Add constants with documentation:
```python
# Target: 23 cosmic + 20 claremont + 22 modern + 20 avengers + 18 characters = 103
COSMIC_ENTITY_TARGET = 23
CLAREMONT_TARGET = 20
# etc.
TOTAL_TARGET = sum([COSMIC_ENTITY_TARGET, CLAREMONT_TARGET, ...])
```

---

### Issue #14: No Logging - Only Print Statements
**Severity**: LOW  
**Location**: Throughout orchestrator

**Problem**:
All output via `print()`. No log levels, no log files, no structured logging.

**Fix**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marathon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Replace print() with:
logger.info("Starting phase: %s", phase_name)
logger.error("Failed to parse protocol: %s", protocol_id)
```

---

### Issue #15: codex_engine.py Not Integrated
**Severity**: LOW  
**Location**: `codex_engine.py` vs rest of system

**Problem**:
The sophisticated `codex_engine.py` scoring system (Trueness, Tap10, Flow, PCS, RPS, CU) is not connected to the protocol content. The `engine/codex_adapter.py` exists but we haven't verified it works with our protocols.

**Fix**:
1. Verify `codex_adapter.py` implementation
2. Add protocol-to-codex input mapping
3. Include codex scores in protocol evaluation
4. Document how scoring works with comic metaphors

---

## 🎯 RECOMMENDED FIX ORDER

### Phase 1: Critical Data Integration (Day 1)
1. **Fix #1**: Create parser for .txt → knowledge_base.json
2. **Fix #3**: Create real test for parser
3. **Fix #5**: Implement actual protocol loading in VectorDatabaseBuilder

### Phase 2: Schema & Validation (Day 2)  
4. **Fix #2**: Update ProtocolType to be more flexible
5. **Fix #11**: Add validation for .txt protocol format
6. **Fix #10**: Fix progress tracker initialization

### Phase 3: Orchestrator Production-Ready (Day 3)
7. **Fix #4**: Make orchestrator generate real content or document as stub
8. **Fix #8**: Add error handling
9. **Fix #9**: Document Cheetah integration status

### Phase 4: Polish (Day 4)
10. **Fix #14**: Add proper logging
11. **Fix #12**: Consolidate documentation
12. **Fix #13**: Document magic numbers
13. **Fix #6**: Clean up imports

---

## ✅ WHAT'S WORKING WELL

1. **Content Quality**: The 65 protocols in .txt files are detailed and well-structured
2. **Schema Design**: `engine/schema.py` has comprehensive data models
3. **4-Dimension Framework**: Consistent D1-D4 analysis across all protocols
4. **Existing Infrastructure**: Pipeline architecture in `engine/` is solid
5. **Documentation**: Thorough markdown documentation
6. **Progress Tracking**: JSON-based progress persistence is good design

---

## 📋 ACTION ITEMS CHECKLIST

```
[ ] Create protocol_parser.py to extract data from .txt files
[ ] Update knowledge_base.json with 65 parsed protocols
[ ] Add real tests in tests/ directory
[ ] Make VectorDatabaseBuilder actually parse files
[ ] Update ProtocolType enum or change to string-based
[ ] Add validation for .txt protocol format
[ ] Fix progress tracker to count existing protocols
[ ] Add error handling to file operations
[ ] Add proper logging
[ ] Document Cheetah integration status
[ ] Consolidate documentation files
[ ] Verify codex_engine integration
```

---

## 🏗️ ARCHITECTURE RECOMMENDATION

Current state has content and code disconnected:

```
CURRENT (Broken):
comic_books/*.txt  →  (no parser)  →  knowledge_base.json (empty)
                                              ↓
                                        engine/ingest.py (doesn't read our format)
```

Should be:

```
RECOMMENDED:
comic_books/*.txt  →  protocol_parser.py  →  knowledge_base.json (populated)
                                                     ↓
                                               engine/ingest.py (reads JSON)
                                                     ↓
                                               Vector DB + Embeddings
                                                     ↓
                                               metaphor_engine.py
                                                     ↓
                                               Applications (podcast, marketing, etc.)
```

---

**Next Step**: Run the fix for Issue #1 - Create protocol parser to sync .txt content to knowledge_base.json

This is the blocking issue that prevents the rest of the system from working.