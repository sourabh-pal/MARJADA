"""GUI-compatible entry point for semantic REMOVE propagation."""
from propagation import adapt


def automatic_remove(engine, feature, choose, choose_paths=None):
    return adapt(engine, 'REMOVE', feature, choose, choose_paths)
