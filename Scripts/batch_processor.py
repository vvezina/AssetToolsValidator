"""
Batch Asset Processor for Unreal Engine

Processes issues flagged by the Asset Validator:
- Rename assets to match naming conventions
- Cap oversized textures to 4096x4096
- Add simple box collision to Static Meshes missing collision
- Auto-generate LODs for Static Meshes with no LODs defined
"""
import unreal
import json

class BatchProcessor:

    def __init__(self):
        pass

    def process(self, validation_results):
        """Route each issue to its handler and collect results."""
        actions = []

        for issues in validation_results["issues"]:

            # Fix naming convention issues (missing or incorrect prefix/suffix)
            if issues["issue_type"] == "naming_prefix":
                actions.append(self._process_naming_issue(issues))

            elif issues["issue_type"] == "naming_suffix":
                actions.append(self._process_naming_issue(issues))

            # Cap oversized textures
            elif issues["issue_type"] == "texture_dimensions":
                actions.append(self._process_texture_issue(issues))

            # Add box collision to Static Meshes missing collision
            elif issues["issue_type"] == "collision":
                actions.append(self._process_collision_issue(issues))

            # Generate LODs for Static Meshes
            elif issues["issue_type"] == "lod":
                actions.append(self._process_lod_issue(issues))

        return actions

    def _process_naming_issue(self, issue):
        """Rename an asset to match the expected naming convention."""
        result = {}

        # Extract the path components needed to build the new name
        base_path = "/".join(issue["asset_path"].split("/")[:-1])
        base_name = issue["base_name"]
        prefix = issue["expected_prefix"]
        variant_suffix = issue["variant_suffix"]

        # If the asset already has a valid variant suffix, keep it
        if variant_suffix:
            suggested_name = f"{base_path}/{prefix}{base_name}_{variant_suffix}"
        # Otherwise, find an available name with an incremented suffix
        else:
            suggested_name = _get_available_name(base_path, prefix, base_name)

        # Rename the asset and track whether it succeeded
        success = unreal.EditorAssetLibrary.rename_asset(issue["asset_path"], suggested_name)

        new_name = suggested_name.split("/")[-1]
        result["success"] = success
        result["log"] = f"[Renamed] {issue['asset_path']} -> {new_name}"

        return result

    def _process_texture_issue(self, issue):
        """Cap a texture's max size to 4096 and save the asset."""
        result = {}
        loaded_asset = unreal.EditorAssetLibrary.load_asset(issue["asset_path"])

        # set_editor_property returns None, so we use try/except to track success
        try:
            loaded_asset.set_editor_property("max_texture_size", 4096)
            unreal.EditorAssetLibrary.save_asset(issue["asset_path"])
            success = True
        except:
            success = False

        result["success"] = success
        result["log"] = f"[Resized] {issue['asset_path']} - Set max texture size to 4096x4096"

        return result

    def _process_collision_issue(self, issue):
        """Add a simple box collision to a static mesh asset."""
        result = {}
        loaded_asset = unreal.EditorAssetLibrary.load_asset(issue["asset_path"])

        try:
            unreal.EditorStaticMeshLibrary.add_simple_collisions(loaded_asset, unreal.ScriptingCollisionShapeType.BOX)
            unreal.EditorAssetLibrary.save_asset(issue["asset_path"])
            success = True
        except:
            success = False

        result["success"] = success
        result["log"] = f"[Collision Added] {issue['asset_path']} - Simple box collision added"

        return result

    def _process_lod_issue(self, issue):
        """Auto-generate LODs with progressive triangle reduction for a static mesh asset."""
        result = {}
        loaded_asset = unreal.EditorAssetLibrary.load_asset(issue["asset_path"])

        try:
            # LOD0: base mesh (100%), LOD1: 50%, LOD2: 25%
            lod0 = unreal.StaticMeshReductionSettings()
            lod0.percent_triangles = 1.0

            lod1 = unreal.StaticMeshReductionSettings()
            lod1.percent_triangles = 0.5

            lod2 = unreal.StaticMeshReductionSettings()
            lod2.percent_triangles = 0.25

            # Build the reduction options with all LOD settings
            reduction_options = unreal.StaticMeshReductionOptions()
            reduction_options.reduction_settings = [lod0, lod1, lod2]
            reduction_options.auto_compute_lod_screen_size = True

            subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            subsystem.set_lods(loaded_asset, reduction_options)
            unreal.EditorAssetLibrary.save_asset(issue["asset_path"])
            success = True
        except:
            success = False

        result["success"] = success
        result["log"] = f"[LOD Generated] {issue['asset_path']} - Auto-generated 2 LODs (50%, 25%)"

        return result



def process_project_assets(results_json, log_window_widget=None, log_scroll_box_widget=None):
    """
    Entry point for the Batch Asset Processor tool.

    Called from Blueprint to:
    1. Receive results from Asset Validator
    2. Process assets based on validation results
    3. Write a summary and each action taken to the UI log window
    4. Return the processing results
    """
    results = json.loads(results_json)
    processor = BatchProcessor()
    actions = processor.process(results)
    _update_log_window(log_window_widget, log_scroll_box_widget, actions)
    return



# ============================================================================
# Helper Functions
# ============================================================================

def _get_available_name(base_path, prefix, base_name):
    """Find next available name by incrementing suffix letter (A, B, C...)."""
    suffix = ord('A')
    while True:
        new_name = f"{prefix}{base_name}_{chr(suffix)}"
        full_path = f"{base_path}/{new_name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(full_path):
            return full_path
        suffix += 1


def _update_log_window(log_window_widget, log_scroll_box_widget, actions):
    """Append batch processing results to the existing log window text."""
    if log_window_widget is None:
        return

    existing_log = str(log_window_widget.get_text())
    log_window_widget.set_text(existing_log + "\n" + _build_log_window_text(actions))

    # Scroll to the bottom so the latest results are visible
    if log_scroll_box_widget is not None:
        log_scroll_box_widget.scroll_to_end()


def _build_log_window_text(actions):
    """Format the list of actions into a human-readable log string."""
    lines = [
        "",
        "Batch Processor: complete.",
    ]

    # Count successes and failures
    valid_actions = [a for a in actions if a is not None]
    succeeded = sum(1 for a in valid_actions if a['success'])
    failed = len(valid_actions) - succeeded

    # Summary line
    lines.append(f"Actions: {len(valid_actions)} | Succeeded: {succeeded} | Failed: {failed}")
    lines.append("")

    # List each action with its result
    if not valid_actions:
        lines.append("No actions taken.")
    else:
        for action in valid_actions:
            if action['success']:
                lines.append(action['log'])
            else:
                lines.append(f"[FAILED] {action['log']}")

    return "\n".join(lines)
