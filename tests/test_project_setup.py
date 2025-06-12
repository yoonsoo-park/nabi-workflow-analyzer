# tests/test_project_setup.py
import unittest
import os

class TestProjectStructure(unittest.TestCase):
    def setUp(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def test_core_directories_exist(self):
        dirs_to_check = [
            "config",
            "data",
            "data/raw_workflows",
            "data/processed_data",
            "docs",
            "n8n_analyzer",
            "n8n_analyzer/core",
            "n8n_analyzer/api",
            "n8n_analyzer/infrastructure",
            "n8n_analyzer/patterns",
            "n8n_analyzer/utils",
            "notebooks",
            "scripts",
            "tests",
            "tests/core",
            "tests/api"
        ]
        for dir_name in dirs_to_check:
            path = os.path.join(self.project_root, dir_name)
            self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist.")

    def test_key_files_exist(self):
        files_to_check = [
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            ".gitignore",
            "config/app_config.py",
            "n8n_analyzer/__init__.py",
            "n8n_analyzer/core/__init__.py",
            "n8n_analyzer/core/models.py",
            "n8n_analyzer/core/parser.py", # Assuming this is now populated by user's fix
            "n8n_analyzer/batch_processor.py",
            "scripts/generate_sample_workflows.py",
            "scripts/setup_db.sql",
            "docs/redis_setup.md"
        ]
        for file_name in files_to_check:
            path = os.path.join(self.project_root, file_name)
            self.assertTrue(os.path.isfile(path), f"File {path} does not exist.")

class TestDependencies(unittest.TestCase):
    def test_import_dependencies(self):
        try:
            import pandas
            import networkx
            import mlxtend
            import ujson
            import flask
            import redis
            import psycopg2
            # import python-dotenv # dotenv is imported in config, not directly typically
        except ImportError as e:
            self.fail(f"Failed to import a core dependency: {e}")
        self.assertTrue(True, "Successfully imported core dependencies.")

if __name__ == '__main__':
    unittest.main()
