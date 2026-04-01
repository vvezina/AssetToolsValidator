"""
Batch Asset Processor for Unreal Engine

Handles bulk operations on assets:
- Rename assets
- Set properties (compression, LOD, collision)
- Process textures in batch
- Organize assets into folders
- Apply metadata/tags
- Fix issues from Asset Validator
"""
import unreal
import json
import re

class BatchProcessor:

    def __init__(self):
        pass
    
    def process(self, validation_results):
        for issues in validation_results["issues"]:

            if issues["issue_type"] == "naming":
                self._process_naming_issue(issues)
                
            elif issues["issue_type"] == "texture_dimensions":
                self._process_texture_issue(issues)

            elif issues["issue_type"] == "collision":
                self._process_collision_issue(issues)
            # Add more issue types as needed              
        return
    
    def _process_naming_issue(self, issue):
        asset_path = issue["asset_path"].split("/")[:-1]
        base_path = "/".join(asset_path)
        asset_name = issue["asset_name"]

        cleaned_name = re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', asset_name).strip('_')
        prefix = issue["expected_prefix"]
        suffix = cleaned_name.rsplit('_', 1)[-1] 
        if suffix.isalpha() and suffix.isupper():
            pass
        else:
            suggested_name = prefix + cleaned_name + '_' + "A"
            suggested_name = self._get_available_name(base_path, prefix, cleaned_name)

        print(suggested_name)
            
            


        # suggested_name = issue["suggested_name"]
        # # Unreal API call to rename asset
        # unreal.EditorAssetLibrary.rename_asset(asset_path, suggested_name)
        # return

    def _get_available_name(self, base_path, prefix, name):
        """Find next available name by incrementing suffix letter."""
        suffix = ord('A')
        while True:
            new_name = f"{prefix}{name}_{chr(suffix)}"
            full_path = f"{base_path}/{new_name}"
            if not unreal.EditorAssetLibrary.does_asset_exist(full_path):
                return full_path
            suffix += 1



    def _process_texture_issue(self, issue):
        pass

    def _process_collision_issue(self, issue):
        pass
    
        

def process_project_assets(results_json, log_window_widget=None):
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
    processor.process(results)
    return



# ============================================================================
# Helper Functions
# ============================================================================

# def _build_log_window_text(results):
#     currentLogText = log_window_widget.get_text()  # Get existing text to append to
#     currentLogText.append(results)  # Append summary
#     return