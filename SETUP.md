# Setup Instructions

## Prerequisites
- Unreal Engine 5.0+
- Python 3.9+ (Unreal Engine Python support enabled)

## Quick Start

### 1. Open the Validator Widget
1. In Unreal Editor, navigate to **Content Browser**
2. Open `EUW_AssetValidator` (Editor Utility Widget)
3. Click **"Validate Asset"** to scan for issues
4. Click **"Fix Assets"** to automatically fix all detected issues

Results display in the widget's scrollable log window.

### 2. Test with Sample Assets
Test assets with intentional naming/dimension errors are included in `Content/TestAssets/`:

- `T_Stone_D` — Example texture asset (may have naming or dimension issues)
- Additional test assets with various violations

Run the validator to see detected issues.

### Setup Details

The Python scripts are located in:
```
Scripts/asset_validator.py    — Validation logic
Scripts/batch_processor.py    — Batch fix logic
```

The Blueprint Editor Utility Widget:
```
Content/Tools/AssetValidator/UI/EUW_AssetValidator.uasset
```

The widget calls `asset_validator.validate_project_assets()` to scan and `batch_processor.process_project_assets()` to fix issues. Both functions accept a log window text widget and a scroll box widget for UI output.

---

## Validation Rules

### Naming Conventions
- **StaticMesh** → `SM_*`
- **Texture2D** → `T_*`
- **Material** → `M_*`
- **Blueprint** → `BP_*`
- **Material Instance** → `MI_*`
- **DataAsset** → `DA_*` (including Blueprint-based subclasses)

### Naming Suffixes
- Numeric suffixes (e.g. `_01`, `_02`) are flagged as invalid
- Alphabetic variant suffixes (e.g. `_A`, `_B`, `_AB`) are valid and preserved during fixes

### Texture Dimensions
- Maximum: **4096x4096 pixels**
- Issues reported if either dimension exceeds this limit

### Collision (Static Meshes)
- All Static Meshes must have simple collision data defined
- Supported collision types: Box, Sphere, Capsule (Sphyl), Convex, Tapered Capsule
- Issues reported if no collision shapes are found

### LOD (Static Meshes)
- All Static Meshes must have at least 3 LODs (LOD0, LOD1, LOD2)
- Issues reported if the mesh has fewer than 3 LODs

---

## Batch Processor Fixes

When "Fix Assets" is clicked, the batch processor applies the following fixes:

| Issue Type | Fix Applied |
|---|---|
| Missing prefix | Renames asset with the correct prefix |
| Numeric suffix | Renames asset with an alphabetic variant suffix |
| Oversized texture | Caps max texture size to 4096x4096 |
| Missing collision | Adds a simple box collision from the mesh's bounding box |
| Missing LODs | Auto-generates LOD1 (50% triangles) and LOD2 (25% triangles) |

---

## Extending the Tool

To add new validators:

1. Add a new method to `AssetValidator` class:
   ```python
   def validate_new_rule(self, asset_data):
       issues = []
       # Your validation logic here
       return issues
   ```

2. Call it in `AssetRegistryScanner.scan_assets()`:
   ```python
   if asset_class == "YourClass":
       all_issues.extend(self.asset_validator.validate_new_rule(asset_data))
   ```

3. Add a handler in `BatchProcessor` to fix the issue:
   ```python
   def _process_new_issue(self, issue):
       result = {}
       # Your fix logic here
       result["success"] = True
       result["log"] = f"[Fixed] {issue['asset_path']} - Description of fix"
       return result
   ```

4. Route the issue type in `BatchProcessor.process()`:
   ```python
   elif issues["issue_type"] == "new_rule":
       actions.append(self._process_new_issue(issues))
   ```

---

## Troubleshooting

**Script not found:**
- Ensure `Scripts/asset_validator.py` exists in project root
- Check Python paths in Execute Python Script node

**Texture validation fails:**
- Asset may not be loaded into memory yet
- Try loading the texture asset manually first

**Performance:**
- For large projects, validation may take a few seconds
- AssetRegistry scanning is optimized and doesn't load assets into memory
