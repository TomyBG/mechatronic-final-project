import os
import json

class ProjectFileManager:
    """
    Handles all file system operations: ensuring directories exist,
    saving data to JSON, and scanning/loading files.
    """
    def __init__(self, root=None):
        self.projects_dir = 'projects/saves'
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def save_project(self, name, data):
        # Ensure correct extension
        if not name.endswith('.json'):
            filename = name + '.json'
        else:
            filename = name
            
        filepath = os.path.join(self.projects_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True, f"Project '{name}' saved successfully."
        except Exception as e:
            return False, str(e)

    def load_project(self, name):
        # Handle cases where name might or might not have extension
        filename = name if name.endswith('.json') else name + '.json'
        filepath = os.path.join(self.projects_dir, filename)
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    def get_existing_projects(self):
        """Scans the directory and returns a list of project names without extensions."""
        files = []
        if os.path.exists(self.projects_dir):
            for f in os.listdir(self.projects_dir):
                if f.endswith('.json'):
                    files.append(os.path.splitext(f)[0])
        return files