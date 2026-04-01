# Setup Instructions

## Prerequisites
- Unreal Engine 5.0+
- Python 3.9+ (Unreal Engine Python support enabled)

## Quick Start

### 1. Open the Validator Widget
1. In Unreal Editor, navigate to **Content Browser**
2. Open `EUW_AssetValidator` (Editor Utility Widget)
3. Click **"Validate Asset"** to scan for issues
4. Click **"Fix Assets"** to automatically rename assets with naming issues

Results display in the widget's text box.

### 2. Test with Sample Assets
Test assets with intentional naming/dimension errors are included in `Content/TestAssets/`:

- `T_Stone_D` — Example texture asset (may have naming or dimension issues)
- Additional test assets with various violations

Run the validator to see detected issues.

### Setup Details

The Python scripts are located in:
```
Scripts/asset_validator.py    — Validation logic
Scripts/batch_processor.py    — Batch fix/rename logic
```

The Blueprint Editor Utility Widget:
```
Content/Tools/AssetValidator/UI/EUW_AssetValidator.uasset
```

The widget calls `asset_validator.validate_project_assets()` to scan and `batch_processor.process_project_assets()` to fix issues.

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
- All Static Meshes must have collision data defined
- Supported collision types: Box, Sphere, Capsule (Sphyl), Convex, Tapered Capsule
- Issues reported if no collision shapes are found

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
