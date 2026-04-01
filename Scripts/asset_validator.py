"""
Asset Validator Tool - Validates Unreal Engine assets for naming, dimensions, and collision compliance.

Validators:
- Naming conventions: Detects missing prefixes (SM_, T_, M_, DA_, BP_, MI_)
- Texture dimensions: Checks that textures do not exceed 4096x4096 resolution
- Collision: Ensures Static Meshes have collision data defined

Results are reported to the calling UI widget.
"""

import unreal
import json


class AssetValidator:
    """Validates individual assets for naming, dimensions, and collision."""

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

        if required_prefix and not asset_name.startswith(required_prefix):
            issues.append({
                "type": "naming",
                "message": f"Invalid name '{asset_name}'. Expected prefix '{required_prefix}'.",
                "expected_prefix": required_prefix
            })

        return issues

    def validate_texture_dimensions(self, asset_data):
        """Validate that textures do not exceed the 4K size limit."""
        issues = []

        texture_asset = asset_data.get_asset()
        if texture_asset is None:
            issues.append({
                "type": "texture_dimensions",
                "message": "Could not load texture asset to validate dimensions."
            })
            return issues

        width = texture_asset.blueprint_get_size_x()
        height = texture_asset.blueprint_get_size_y()

        if width > 4096 or height > 4096:
            issues.append({
                "type": "texture_dimensions",
                "message": f"Texture dimensions exceed 4K: {width}x{height}. Maximum is 4096x4096."
            })

        return issues

    def validate_collision(self, asset_data):
        """Validate that a Static Mesh has simple collision data."""
        issues = []

        # Load the Static Mesh asset
        mesh_asset = asset_data.get_asset()
        if mesh_asset is None:
            issues.append({
                "type": "collision",
                "message": "Could not load Static Mesh asset to validate collision."
            })
            return issues

        # Get the BodySetup (contains collision data)
        body_setup = mesh_asset.get_editor_property("body_setup")
        if body_setup is None:
            issues.append({
                "type": "collision",
                "message": "Static Mesh has no BodySetup, so no collision data was found."
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
                "type": "collision",
                "message": "Static Mesh has no collision defined."
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

    COLLISION_CHECK_CLASSES = {
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

            # Skip asset classes we don't care about, but check if unknown
            # classes might be DataAsset subclasses before discarding
            if asset_class not in self.RELEVANT_CLASSES:
                if not _is_data_asset(asset_data):
                    continue

            total_count += 1

            all_issues = []

            all_issues.extend(self.asset_validator.validate_naming(asset_data))

            # Check texture dimensions
            if asset_class == "Texture2D":
                all_issues.extend(self.asset_validator.validate_texture_dimensions(asset_data))

            # Check collision for Static Meshes
            if asset_class in self.COLLISION_CHECK_CLASSES:
                all_issues.extend(self.asset_validator.validate_collision(asset_data))  

            # Collect results — forward any extra fields (e.g. expected_prefix)
            # from validators so the batch processor can use them
            if all_issues:
                invalid_count += 1
                for issue in all_issues:
                    entry = {
                        "asset_name": str(asset_data.asset_name),
                        "asset_path": str(asset_data.package_name),
                        "asset_class": asset_class,
                        "message": issue["message"],
                        "issue_type": issue["type"],
                    }
                    if "expected_prefix" in issue:
                        entry["expected_prefix"] = issue["expected_prefix"]
                    issues.append(entry)
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



def validate_project_assets(log_window_widget=None):
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
    _update_log_window(log_window_widget, results)

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


def _update_log_window(log_window_widget, results):
    if log_window_widget is None:
        return

    log_window_widget.set_text(_build_log_window_text(results))


def _build_log_window_text(results):
    summary = results["summary"]
    issues = results["issues"]

    lines = [
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
