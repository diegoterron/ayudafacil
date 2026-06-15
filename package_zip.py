import os
import zipfile
import fnmatch

def get_ignore_list():
    # Base standard ignore patterns
    patterns = [
        '.git',
        '.venv',
        'node_modules',
        '__pycache__',
        '.pytest_cache',
        'dist',
        'dist-ssr',
        '.idea',
        '.vscode',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        'tfg_demo.zip',
        'package_zip.py',
        '*.log',
        '.env',
        '.env.*',
        '*.local'
    ]
    # Read .gitignore rules if present
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Strip trailing slash for consistency in fnmatch
                    if line.endswith('/'):
                        line = line[:-1]
                    patterns.append(line)
    return list(set(patterns))

def should_ignore(path, ignore_patterns):
    parts = path.split(os.sep)
    for part in parts:
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(part, pattern):
                return True
            # Match folder prefixes too
            if '/' in pattern:
                norm_pat = pattern.replace('/', os.sep)
                if fnmatch.fnmatch(path, norm_pat) or path.startswith(norm_pat + os.sep):
                    return True
    return False

def package_project():
    zip_name = 'tfg_demo.zip'
    ignore_patterns = get_ignore_list()
    
    print(f"Empaquetando proyecto en '{zip_name}'...")
    print(f"Patrones de exclusión activos: {ignore_patterns}\n")
    
    file_count = 0
    ignored_count = 0
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Prune directories in-place to avoid deep traversal
            dirs_to_keep = []
            for d in dirs:
                dir_path = os.path.join(root, d)
                rel_path = os.path.relpath(dir_path, '.')
                if not should_ignore(rel_path, ignore_patterns):
                    dirs_to_keep.append(d)
                else:
                    ignored_count += 1
            dirs[:] = dirs_to_keep
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, '.')
                if not should_ignore(rel_path, ignore_patterns):
                    zipf.write(file_path, rel_path)
                    print(f" [+] Añadido: {rel_path}")
                    file_count += 1
                else:
                    ignored_count += 1
                    
    print(f"\n¡Empaquetado finalizado con éxito!")
    print(f"Total archivos comprimidos: {file_count}")
    print(f"Total carpetas/archivos omitidos: {ignored_count}")
    print(f"Archivo de entrega generado: {os.path.abspath(zip_name)}")

if __name__ == '__main__':
    package_project()
