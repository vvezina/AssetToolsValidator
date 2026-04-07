# Asset Tools Validator

Asset validation and batch processing tool built in Unreal Engine using Editor Utility Widgets and Python.

Designed to detect common pipeline issues and fix them directly inside the editor in one pass.

## Why

I built this tool to focus on Unreal tools development using Python.

The goal was to show the workflow between Python and Editor Utility Widgets, while keeping the tool simple and practical.

It covers a few common checks (naming, textures, etc.) that most projects need, but structured in a way that can be easily extended.

## Preview

![Issues Detected](Screenshots/AssetValidator_A.png)  
![All Fixed](Screenshots/AssetValidator_D.png)

<details>
<summary>Animated demo (GIF)</summary>

![Asset Validator Demo](Screenshots/AssetValidatorGif.gif)

</details>

## What it does

Scans a selected folder and validates assets for common issues:

- Naming conventions (`SM_`, `T_`, `M_`, `DA_`, `BP_`, `MI_`)  
- Invalid numeric suffixes  
- Texture size limits (max 4096x4096)  
- Missing collision on Static Meshes  
- Missing LODs (requires at least LOD0–LOD2)  
- Detects Blueprint-based DataAsset subclasses via asset registry  

## Batch Processing

Fixes all detected issues in one pass:

- Renames assets to match conventions  
- Resizes oversized textures  
- Generates simple collision from bounding box  
- Auto-generates LODs (50% / 25%)  

## Architecture

Editor Utility Widget (UI)  
→ Python validator (`asset_validator.py`)  
→ Python batch processor (`batch_processor.py`)  

Flow:  
Validate → scan & report issues → Fix → apply batch corrections  

## Constraints / Decisions

- Python used for validation and processing to leverage Unreal’s editor scripting API  
- UI kept in Blueprint (EUW) for fast iteration  
- Designed to handle large folders (1000+ assets)  
- Validation and fixing split into separate steps for clarity and control  
- Built primarily in Python to demonstrate tooling workflows outside of Blueprint/C++  

## Setup

1. Open the project in Unreal Engine 5.7  
2. Enable the Python plugin  
3. Open the Editor Utility Widget "EUW_AssetValidator" to validate and fix assets  

## Tech

- Unreal Engine 5.7  
- Python (Unreal Python API)  
- Blueprint (Editor Utility Widget)  
