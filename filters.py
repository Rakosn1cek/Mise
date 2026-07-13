# filters.py

# High-risk executive scripts and source files
SCRIPT_EXTENSIONS = {
    # Shell scripts
    ".sh", ".bash", ".zsh", ".ksh", ".csh", ".fish", ".local",
    
    # Scripting languages
    ".py", ".pyw", ".pl", ".rb", ".lua", ".tcl", ".pyi",
    
    # Systems & Compiled languages
    ".c", ".cpp", ".cc", ".h", ".hpp", ".rs", ".go", ".js", ".ts"
}

def is_target_script(file_name):
    """
    Checks if the given file name matches our developer security filters.
    Extracts the extension reliably even if double extensions occur (like .sh.txt).
    """
    if not file_name:
        return False
        
    name_lower = file_name.lower()
    
    # Check standard single extensions
    for ext in SCRIPT_EXTENSIONS:
        if name_lower.endswith(ext):
            return True
            
    return False
