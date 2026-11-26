"""GUI-compatible entry point for semantic ADD propagation."""
from propagation import adapt


def automatic_add(engine, feature, choose, choose_paths=None):
    return adapt(engine, 'ADD', feature, choose, choose_paths)
