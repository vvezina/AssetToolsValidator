# Asset Validator Tool (Unreal Engine + Python)

**Status: Work in Progress**

## Overview
Lightweight asset validation tool built using Unreal Engine Editor Utility Widgets and Python.

Designed to enforce naming conventions and detect common pipeline issues directly inside the editor.

---

## Features (Current)
- **Naming Convention Validation** — Detects missing asset prefixes (`SM_`, `T_`, `M_`, `DA_`, `BP_`, `MI_`) and invalid numeric suffixes
- **DataAsset Subclass Detection** — Correctly identifies Blueprint-based DataAsset subclasses in the asset registry
- **Texture Dimension Validation** — Checks that textures do not exceed 4096x4096 resolution
- **Collision Validation** — Ensures Static Meshes have collision data defined
- **Batch Asset Processor** — Automatically renames assets to fix naming issues (prefix and suffix)
- **Asset Registry Scanning** — Fast, non-destructive scanning using Unreal's AssetRegistry API
- **One-click Validation & Fix** — Integrated Editor Utility Widget with Validate and Fix Assets buttons

---

## Preview

![Asset Validator Widget](Screenshots/AssetValidator.png)

---

## Architecture
- **UI Layer:** Editor Utility Widget (Blueprint)
- **Validation Layer:** Python — `asset_validator.py` (Unreal Python API)
- **Processing Layer:** Python — `batch_processor.py` (Unreal Python API)
- **Flow:** Validate button → scan & report issues → Fix Assets button → batch rename/fix

---

## Tech Stack
- Unreal Engine (Editor Utility Widgets)
- Python (Unreal Python API)

---

## Purpose
Demonstrates pipeline tooling and asset validation practices used in production environments.