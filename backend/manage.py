#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Tenter de détecter et d'utiliser automatiquement l'environnement virtuel local (venv)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        
        # Chemins potentiels du venv
        venv_candidates = [
            os.path.join(parent_dir, 'venv'),
            os.path.join(parent_dir, '.venv'),
            os.path.join(base_dir, 'venv'),
            os.path.join(base_dir, '.venv'),
        ]
        
        venv_found = False
        for venv_path in venv_candidates:
            if os.path.exists(venv_path):
                if sys.platform == 'win32':
                    python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
                else:
                    python_exe = os.path.join(venv_path, 'bin', 'python')
                
                if os.path.exists(python_exe):
                    # Éviter une boucle infinie de ré-exécution
                    if os.environ.get('DJANGO_AUTOVENV_RUNNING') != '1':
                        os.environ['DJANGO_AUTOVENV_RUNNING'] = '1'
                        result = subprocess.run([python_exe] + sys.argv, close_fds=False)
                        sys.exit(result.returncode)
        
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

