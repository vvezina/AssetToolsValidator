"""
Asset Validator Tool - Validates Unreal Engine assets for naming, dimensions, collision, and LOD compliance.

Validators:
- Naming conventions: Detects missing prefixes (SM_, T_, M_, DA_, BP_, MI_) and invalid numeric suffixes
- Texture dimensions: Checks that textures do not exceed 4096x4096 resolution
- Collision: Ensures Static Meshes have collision data defined
- LOD: Ensures Static Meshes have at least 3 LODs (LOD0, LOD1, LOD2)

Results are reported to the calling UI widget.
"""

import unreal
import json
import re

class AssetValidator:
    """Validates individual assets for naming, dimensions, collision, and LODs."""

    REQUIRED_PREFIXES = {
        "StaticMesh": "SM_",
        "Texture2D": "T_",
        "Material": "M_",
        "DataAsset": "DA_",
        "Blueprint": "BP_",
        "MaterialInstanceConstant": "MI_",
    }

    def validate_naming(self, asset_data):
        """Validate naming conventions for a single asset."""
        issues = []

        asset_name = str(asset_data.asset_name)
        asset_class = _get_asset_class(asset_data)
        required_prefix = self.REQUIRED_PREFIXES.get(asset_class)

        # DataAssets can appear as "Blueprint" (the parent BP) or as a custom
        # class like "DA_TestData_C" (child instances). When the class isn't
        # recognized or is "Blueprint", check inheritance to apply DA_ prefix.
        if not required_prefix or asset_class == "Blueprint":
            if _is_data_asset(asset_data):
                required_prefix = "DA_"

        parsed = _parse_asset_name(asset_name, required_prefix)

        # Check if the asset is missing its required prefix
        if required_prefix and not asset_name.startswith(required_prefix):
            issues.append({
                "issue_type": "naming_prefix",
                "message": f"Invalid name '{asset_name}'. Expected prefix '{required_prefix}'.",
                "expected_prefix": required_prefix,
                "base_name": parsed["base_name"],
                "variant_suffix": parsed["variant_suffix"],
            })

        # Check if the asset name ends with a numeric suffix (e.g. _01)
        if asset_name.split("_")[-1].isdigit():
            issues.append({
                "issue_type": "naming_suffix",
                "message": f"Asset name '{asset_name}' should not end with a numeric suffix (e.g. '_01').",
                "expected_prefix": required_prefix,
                "base_name": parsed["base_name"],
                "variant_suffix": parsed["variant_suffix"],
            })

        return issues

    def validate_texture_dimensions(self, asset_data):
        """Validate that textures do not exceed the 4K size limit."""
        issues = []

        # Load the texture asset
        texture_asset = asset_data.get_asset()
        if texture_asset is None:
            issues.append({
                "issue_type": "texture_dimensions",
                "message": "Could not load texture asset to validate dimensions.",
            })
            return issues

        # Check if either dimension exceeds 4096
        width = texture_asset.blueprint_get_size_x()
        height = texture_asset.blueprint_get_size_y()

        if width > 4096 or height > 4096:
            issues.append({
                "issue_type": "texture_dimensions",
                "message": f"Texture dimensions exceed 4K: {width}x{height}. Maximum is 4096x4096.",
            })

        return issues

    def validate_collision(self, asset_data):
        """Validate that a Static Mesh has simple collision data."""
        issues = []

        # Load the Static Mesh asset
        mesh_asset = asset_data.get_asset()
        if mesh_asset is None:
            issues.append({
                "issue_type": "collision",
                "message": "Could not load Static Mesh asset to validate collision.",
            })
            return issues

        # Get the BodySetup (contains collision data)
        body_setup = mesh_asset.get_editor_property("body_setup")
        if body_setup is None:
            issues.append({
                "issue_type": "collision",
                "message": "Static Mesh has no BodySetup, so no collision data was found.",
            })
            return issues

        # Get the aggregate geometry (contains all collision shapes)
        agg_geom = body_setup.get_editor_property("agg_geom")

        # Count all simple collision shapes (boxes, spheres, capsules, convex, tapered capsules)
        simple_collision_count = 0
        simple_collision_count += len(agg_geom.get_editor_property("box_elems"))
        simple_collision_count += len(agg_geom.get_editor_property("sphere_elems"))
        simple_collision_count += len(agg_geom.get_editor_property("sphyl_elems"))
        simple_collision_count += len(agg_geom.get_editor_property("convex_elems"))
        simple_collision_count += len(agg_geom.get_editor_property("tapered_capsule_elems"))

        # Issue if no collision shapes exist
        if simple_collision_count == 0:
            issues.append({
                "issue_type": "collision",
                "message": "Static Mesh has no collision defined.",
            })

        return issues

    def validate_lod(self, asset_data):
        """Validate that a Static Mesh has at least 3 LODs (LOD0, LOD1, LOD2)."""
        issues = []

        # Load the Static Mesh asset
        mesh_asset = asset_data.get_asset()
        if mesh_asset is None:
            issues.append({
                "issue_type": "lod",
                "message": "Could not load Static Mesh asset to validate LODs.",
            })
            return issues

        # LOD 0 is the base mesh, so we need at least 3 (LOD0 + LOD1 + LOD2)
        lod_count = unreal.EditorStaticMeshLibrary.get_lod_count(mesh_asset)
        if lod_count < 3:
            issues.append({
                "issue_type": "lod",
                "message": f"Static Mesh has {lod_count} LOD(s), expected at least 3 (LOD0, LOD1, LOD2).",
            })

        return issues


class AssetRegistryScanner:
    """Query the asset registry and collect validation results."""

    # Asset classes to include in the scan. DataAsset subclasses (e.g. DA_TestData_C)
    # won't match these, so they're caught separately via _is_data_asset().
    RELEVANT_CLASSES = {
        "StaticMesh",
        "Texture2D",
        "Material",
        "MaterialInstanceConstant",
        "Blueprint",
        "DataAsset",
    }

    # Asset classes that require collision and LOD validation
    STATIC_MESH_CLASSES = {
        "StaticMesh"
    }

    def __init__(self):
        self.asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        self.asset_validator = AssetValidator()

    def scan_assets(self):
        # Query all assets in /Game
        all_assets = self.asset_registry.get_assets_by_path(
            "/Game", recursive=True, include_only_on_disk_assets=True
        )

        issues = []
        total_count = 0
        valid_count = 0
        invalid_count = 0

        for asset_data in all_assets:
            asset_class = _get_asset_class(asset_data)

            # Resolve DataAssets: they can appear as unknown classes (e.g. DA_TestData_C)
            # or as "Blueprint" in the registry. Reclassify them as "DataAsset".
            if asset_class not in self.RELEVANT_CLASSES:
                if _is_data_asset(asset_data):
                    asset_class = "DataAsset"
                else:
                    continue
            elif asset_class == "Blueprint" and _is_data_asset(asset_data):
                asset_class = "DataAsset"

            total_count += 1

            # Common fields shared by all issues for this asset
            base_entry = {
                "asset_name": str(asset_data.asset_name),
                "asset_path": str(asset_data.package_name),
                "asset_class": asset_class,
            }

            all_issues = []

            # Check naming conventions (prefixes and suffixes)
            all_issues.extend(self.asset_validator.validate_naming(asset_data))

            # Check texture dimensions
            if asset_class == "Texture2D":
                all_issues.extend(self.asset_validator.validate_texture_dimensions(asset_data))

            # Check collision and LODs for Static Meshes
            if asset_class in self.STATIC_MESH_CLASSES:
                all_issues.extend(self.asset_validator.validate_collision(asset_data))
                all_issues.extend(self.asset_validator.validate_lod(asset_data))

            # Merge common fields with each issue and add to results
            if all_issues:
                invalid_count += 1
                for issue in all_issues:
                    issues.append({**base_entry, **issue})
            else:
                valid_count += 1

        return {
            "summary": {
                "total": total_count,
                "valid": valid_count,
                "invalid": invalid_count,
            },
            "issues": issues,
        }



def validate_project_assets(log_window_widget=None, log_scroll_box_widget=None):
    """
    Entry point for the Asset Validator tool.

    Called from Blueprint to:
    1. Create the scanner
    2. Run the scan
    3. Write a summary and each issue to the UI log window
    4. Return the results
    """
    scanner = AssetRegistryScanner()
    results = scanner.scan_assets()
    _update_log_window(log_window_widget, log_scroll_box_widget, results)

    return json.dumps(results)

# ============================================================================
# Helper Functions
# ============================================================================

def _get_asset_class(asset_data):
    """Extract asset class name from asset data."""
    return str(asset_data.asset_class_path.asset_name)


def _is_data_asset(asset_data):
    """Return True if the asset is a DataAsset or inherits from one, False otherwise."""
    loaded = asset_data.get_asset()
    if not loaded:
        return False
    if isinstance(loaded, unreal.Blueprint):
        obj = unreal.get_default_object(loaded.generated_class())
    else:
        obj = loaded
    return isinstance(obj, unreal.DataAsset)


def _update_log_window(log_window_widget, log_scroll_box_widget, results):
    """Append validation results to the existing log window text."""
    if log_window_widget is None:
        return

    existing_log = str(log_window_widget.get_text())
    log_window_widget.set_text(existing_log + "\n" + _build_log_window_text(results))

    # Scroll to the bottom so the latest results are visible
    if log_scroll_box_widget is not None:
        log_scroll_box_widget.scroll_to_end()


def _build_log_window_text(results):
    """Format the validation results into a human-readable log string."""
    summary = results["summary"]
    issues = results["issues"]

    lines = [
        "",
        "Asset Validator: scan complete.",
        (
            f"Total: {summary['total']} | "
            f"Valid: {summary['valid']} | "
            f"Invalid: {summary['invalid']}"
        ),
        "",
    ]

    if not issues:
        lines.append("No issues found.")
    else:
        for issue in issues:
            lines.append(
                f"[{issue['asset_class']}] "
                f"{issue['asset_path']} - {issue['message']}"
            )

    return "\n".join(lines)


def _parse_asset_name(name, expected_prefix):
    """Parse asset name into base name and variant suffix."""
    # Remove expected prefix if it exists
    if expected_prefix and name.startswith(expected_prefix):
        name = name[len(expected_prefix):]

    # Remove non-alphanumeric characters from start and end, but keep underscores
    cleaned_name = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', name).strip('_')

    # Check for trailing variant suffix (e.g. _A, _AB, _ABC — up to 3 letters)
    variant_suffix = None
    parts = cleaned_name.rsplit('_', 1)
    if len(parts) > 1 and parts[-1].isalpha() and parts[-1].isupper() and len(parts[-1]) <= 3:
        cleaned_name = parts[0]
        variant_suffix = parts[-1]

    return {"base_name": cleaned_name, "variant_suffix": variant_suffix}