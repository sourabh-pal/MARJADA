"""Lazy shortest-first enumeration of distinct, cycle-free invocation paths.

Yen's algorithm enumerates progressively; the UI need not enumerate all paths
or claim a total count before the user can choose. Equal-length paths use
lexicographic order. Size means number of edges, not number of missing features.
"""
from collections import deque
from heapq import heappop, heappush


def iter_invocation_paths(edges, roots, target):
    graph = {node: set(children) for node, children in edges.items()}
    if target not in graph:
        return
    start = '__MARJADA_INVOCATION_START__'
    while start in graph:
        start += '_'
    graph[start] = set(roots) & graph.keys()

    def shortest(source, forbidden_nodes=frozenset(), forbidden_edges=frozenset()):
        if source in forbidden_nodes:
            return None
        queue = deque([source])
        parents = {source: None}
        while queue:
            current = queue.popleft()
            if current == target:
                path = []
                while current is not None:
                    path.append(current)
                    current = parents[current]
                return tuple(reversed(path))
            for child in sorted(graph.get(current, ())):
                if (child not in parents and child not in forbidden_nodes
                        and (current, child) not in forbidden_edges):
                    parents[child] = current
                    queue.append(child)
        return None

    first = shortest(start)
    if first is None:
        return
    accepted = [first]
    candidates = []
    known = {first}
    yield first[1:]
    while True:
        previous = accepted[-1]
        for index in range(len(previous) - 1):
            prefix = previous[:index + 1]
            banned_edges = {
                (path[index], path[index + 1])
                for path in accepted
                if len(path) > index + 1 and path[:index + 1] == prefix
            }
            spur = shortest(prefix[-1], frozenset(prefix[:-1]), banned_edges)
            if spur is None:
                continue
            candidate = prefix[:-1] + spur
            if candidate not in known:
                known.add(candidate)
                heappush(candidates, (len(candidate), candidate))
        if not candidates:
            return
        _, following = heappop(candidates)
        accepted.append(following)
        yield following[1:]
