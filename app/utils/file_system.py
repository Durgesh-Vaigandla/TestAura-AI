import os

def ensure_test_folder_ignored(target_directory: str, test_folder: str):
    """
    Ensures that the given test_folder is ignored in the target_directory's .gitignore file.
    Creates the .gitignore if it doesn't exist.
    """
    if not target_directory or not test_folder:
        return
        
    gitignore_path = os.path.join(target_directory, '.gitignore')
    ignore_entry = f"\n# TestAura Auto-Generated\n{test_folder}/\n"
    
    try:
        # Check if the folder is already in the file
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                content = f.read()
                if f"{test_folder}/" in content or test_folder in content.split('\n'):
                    return # Already ignored
        
        # Append to the file (or create it)
        with open(gitignore_path, 'a') as f:
            f.write(ignore_entry)
            
        print(f"Added {test_folder}/ to {gitignore_path}")
    except Exception as e:
        print(f"Failed to update .gitignore in {target_directory}: {e}")
