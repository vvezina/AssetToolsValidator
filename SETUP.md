# Setup Instructions

## Prerequisites
- Unreal Engine 5.0+
- Python 3.9+ (Unreal Engine Python support enabled)

## Quick Start

### 1. Open the Validator Widget
1. In Unreal Editor, navigate to **Content Browser**
2. Open `EUW_AssetValidator` (Editor Utility Widget)
3. Click **"Validate Asset"**

Results display in the widget's text box.

### 2. Test with Sample Assets
Test assets with intentional naming/dimension errors are included in `Content/TestAssets/`:

- `T_Stone_D` — Example texture asset (may have naming or dimension issues)
- Additional test assets with various violations

Run the validator to see detected issues.

### Setup Details

The Python validation logic is located in:
```
Scripts/asset_validator.py
```

The Blueprint Editor Utility Widget:
```
Content/EUW_AssetValidator.uasset
```

The widget calls `asset_validator.validate_project_assets()` and displays results in its text display.

---

## Validation Rules

### Naming Conventions
- **StaticMesh** → `SM_*`
- **Texture2D** → `T_*`
- **Material** → `M_*`
- **Blueprint** → `BP_*`
- **Material Instance** → `MI_*`
- **DataAsset** → `DA_*`

### Texture Dimensions
- Maximum: **4096x4096 pixels**
- Issues reported if either dimension exceeds this limit

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
