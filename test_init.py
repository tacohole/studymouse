import os
import sys
import importlib.machinery
import importlib.util
import unittest

class TestInitModule(unittest.TestCase):
    def test_init_exports(self):
        # Load __init__.py by path so we don't trigger package import side-effects
        path = os.path.join(os.path.dirname(__file__), "__init__.py")
        loader = importlib.machinery.SourceFileLoader("studymouse_init", path)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)

        # Instead of importing the module (which pulls in heavy GUI deps),
        # parse the source and assert the expected symbols are declared.
        import ast

        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()

        tree = ast.parse(src, filename=path)

        has_run = any(isinstance(n, ast.FunctionDef) and n.name == "runKnowtPlugin" for n in tree.body)
        has_window = any(isinstance(n, ast.ClassDef) and n.name == "KnowtWindow" for n in tree.body)

        self.assertTrue(has_run, "runKnowtPlugin should be defined in __init__.py")
        self.assertTrue(has_window, "KnowtWindow should be defined in __init__.py")

if __name__ == '__main__':
    unittest.main()
