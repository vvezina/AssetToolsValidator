# Asset Validator Tool (Unreal Engine + Python)

## Overview
Lightweight asset validation and batch processing tool built using Unreal Engine Editor Utility Widgets and Python.

Designed to enforce naming conventions and detect common pipeline issues directly inside the editor, then automatically fix them in one click.

---

## Features
- **Naming Convention Validation** — Detects missing asset prefixes (`SM_`, `T_`, `M_`, `DA_`, `BP_`, `MI_`) and invalid numeric suffixes
- **DataAsset Subclass Detection** — Correctly identifies Blueprint-based DataAsset subclasses in the asset registry
- **Texture Dimension Validation** — Checks that textures do not exceed 4096x4096 resolution
- **Collision Validation** — Ensures Static Meshes have simple collision data defined
- **LOD Validation** — Ensures Static Meshes have at least 3 LODs (LOD0, LOD1, LOD2)
- **Batch Asset Processor** — Automatically fixes all detected issues:
  - Renames assets to match naming conventions
  - Caps oversized textures to 4096x4096
  - Adds simple box collision from bounding box
  - Auto-generates LODs with progressive triangle reduction (50%, 25%)
- **Asset Registry Scanning** — Fast, non-destructive scanning using Unreal's AssetRegistry API
- **One-click Validation & Fix** — Integrated Editor Utility Widget with Validate and Fix Assets buttons
- **Scrollable Log Output** — Results append to a scrollable log window that auto-scrolls to the latest output

---

## Preview

https://github.com/user-attachments/assets/5a0e76d6-f04b-4dfd-a8cf-95364c4d8ffb

---

## Architecture
- **UI Layer:** Editor Utility Widget (Blueprint)
- **Validation Layer:** Python — `asset_validator.py` (Unreal Python API)
- **Processing Layer:** Python — `batch_processor.py` (Unreal Python API)
- **Flow:** Validate button → scan & report issues → Fix Assets button → batch fix all issues

---

## Tech Stack
- Unreal Engine (Editor Utility Widgets)
- Python (Unreal Python API)

---

## Purpose
Demonstrates pipeline tooling and asset validation practices used in production environments.
