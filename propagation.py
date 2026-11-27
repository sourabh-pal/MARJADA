#Created by Sourabh Pal

from collections import deque
from types import SimpleNamespace
from invocation_paths import iter_invocation_paths


class PropagationError(Exception):
    pass


def adapt(engine, operation, feature, choose, choose_paths=None):
    original = frozenset(engine.configuration.active)
    fm = engine.fm
    features = set(fm.features)
    root = engine.root_feature
    invocations = set(engine.invocation_features)
    structural = {kind: {p: set(cs) for p, cs in fm.structural.get(kind, {}).items()}
                  for kind in ('mandatory', 'optional', 'xor', 'or')}
    requires = {p: set(cs) for p, cs in fm.cross_tree.get('requires', {}).items()}
    excludes = {p: set(cs) for p, cs in fm.cross_tree.get('excludes', {}).items()}
    children = {f: set() for f in features}
    for groups in structural.values():
        for p, cs in groups.items():
            children.setdefault(p, set()).update(cs)
    edges = {f: children.get(f, set()) | requires.get(f, set()) for f in features}
    additions, removals, trace = set(), set(), []

    def effective():
        return (set(original) | additions) - removals

    def reachable(active):
        seen = invocations & active
        queue = deque(seen)
        while queue:
            for node in (edges.get(queue.popleft(), set()) & active) - seen:
                seen.add(node)
                queue.append(node)
        return seen

    def include(node, rule):
        if node not in features:
            raise PropagationError(f'{rule}: unknown feature {node}.')
        if node in removals:
            raise PropagationError(f'{rule}: {node} would belong to both A and R.')
        if node not in original and node not in additions:
            additions.add(node)
            trace.append(f'{rule}: ADD {node}')

    def remove(node, rule):
        if node in additions:
            raise PropagationError(f'{rule}: {node} would belong to both A and R.')
        if node == root or node in invocations:
            raise PropagationError(f'{rule}: cannot remove root/invocation feature {node}.')
        if node not in removals:
            removals.add(node)
            trace.append(f'{rule}: REMOVE {node}')

    def paths_for(target, rule):
        allowed_edges = {p: cs - removals for p, cs in edges.items() if p not in removals}
        iterator = iter_invocation_paths(allowed_edges, invocations, target)
        if choose_paths is None:
            first = next(iterator, None)
            if first is None:
                raise PropagationError(f'No available invocation path to {target}.')
            selected = [first]
        else:
            selected = choose_paths(target, iterator, set(original), fm.structural, fm.cross_tree)
            if selected is None:
                raise PropagationError('Path selection cancelled.')
        if not selected:
            raise PropagationError(f'No invocation path selected for {target}.')
        for raw in selected:
            path = tuple(raw)
            if (not path or path[0] not in invocations or path[-1] != target
                    or len(set(path)) != len(path)
                    or any(p not in allowed_edges for p in path)
                    or any(b not in allowed_edges[a] for a, b in zip(path, path[1:]))):
                raise PropagationError('Invalid invocation path selection.')
            trace.append('Confirmed invocation path: ' + ' -> '.join(path))
            for node in path:
                include(node, rule)

    try:
        if operation not in ('ADD', 'REMOVE') or feature not in features:
            raise PropagationError('Invalid operation or unknown requested feature.')
        if not invocations or not invocations <= original:
            raise PropagationError('Choose active invocation features before adaptation.')
        # Validate the baseline without changing the real Configuration object.
        shadow = SimpleNamespace(active=set(original))
        validator = type(engine)(fm, shadow, root, invocations)
        valid, messages = validator.verify_configuration()
        if not valid:
            raise PropagationError('Initial configuration is invalid: ' + '; '.join(messages))
        if operation == 'ADD':
            if feature in original:
                return True, [f'ADD {feature}: already active; configuration unchanged.']
            include(feature, 'Request+')
            # Confirmed missing path nodes are explicit additional user requests.
            # This preserves multi-path UI even if the target already has a path.
            if choose_paths is not None:
                paths_for(feature, 'PathRequest+')
        else:
            if feature not in original:
                return True, [f'REMOVE {feature}: already inactive; configuration unchanged.']
            remove(feature, 'Request-')

        while True:
            before = (frozenset(additions), frozenset(removals))
            # Saturate deterministic rules before asking for a group choice.
            while True:
                previous = (frozenset(additions), frozenset(removals))
                for parent in sorted(children):
                    for child in sorted(children[parent]):
                        if child in additions and parent not in original | additions and parent not in removals:
                            include(parent, 'Fat+')
                        if parent in removals and child in original - removals and child not in additions:
                            remove(child, 'Fat-')
                for kind, relation in (('M rho+', structural['mandatory']), ('M rho+', requires)):
                    for source in sorted(relation):
                        for target in sorted(relation[source]):
                            if source in additions and target not in original | additions and target not in removals:
                                include(target, kind)
                for source in sorted(requires):
                    for target in sorted(requires[source]):
                        if target in removals and source in original - removals and source not in additions:
                            remove(source, 'rho-')
                for parent, siblings in sorted(structural['xor'].items()):
                    for child in sorted(siblings & additions):
                        for sibling in sorted((siblings - {child}) & (original - removals)):
                            remove(sibling, 'X+ SIB')
                for source in sorted(excludes):
                    for target in sorted(excludes[source]):
                        if source in additions and target in original - removals:
                            remove(target, 'chi+')
                        if target in additions and source in original - removals:
                            remove(source, 'chi-')
                if previous == (frozenset(additions), frozenset(removals)):
                    break

            changed = False
            for kind in ('xor', 'or'):
                for parent, group in sorted(structural[kind].items()):
                    # Literal premise from the supplied figure: C union A, not E.
                    if parent in additions and not group & (original | additions):
                        candidates = sorted(group - removals)
                        if not candidates:
                            raise PropagationError(f'{kind.upper()} {parent}: no permitted child.')
                        if len(candidates) == 1:
                            answer = {candidates[0]}
                        else:
                            answer = choose(f'{kind.upper()} for {parent}: choose one child',
                                            candidates, False, set())
                            if answer is None:
                                raise PropagationError('Feature selection cancelled.')
                            answer = set(answer)
                            if len(answer) != 1 or not answer <= set(candidates):
                                raise PropagationError('Choose exactly one permitted child.')
                        include(next(iter(answer)), 'OrX+ FAT')
                        changed = True
                        break
                if changed:
                    break
            if changed:
                continue
            reached = reachable(effective())
            missing = sorted(additions - reached - {root})
            if missing:
                old_count = len(additions)
                paths_for(missing[0], 'IP+')
                if len(additions) == old_count:
                    raise PropagationError(f'IP+: selected path makes no progress for {missing[0]}.')
                continue
            # REMOVE repair extension: keep surviving active XOR/OR parents valid.
            # Do this before unreachable cleanup so replacement paths can retain
            # features which are still useful in the resulting configuration.
            if operation == 'REMOVE':
                repaired = False
                for kind in ('xor', 'or'):
                    for parent, group in sorted(structural[kind].items()):
                        if (parent not in effective() or parent not in reached | {root}
                                or group & effective()):
                            continue
                        candidates = sorted(group - removals)
                        if not candidates:
                            raise PropagationError(f'{kind.upper()} {parent}: no permitted replacement.')
                        multiple = kind == 'or'
                        # A two-child XOR has one forced alternative. Larger
                        # groups retain user choice even if removals narrow it.
                        prompt = multiple or len(group) > 2 or len(candidates) > 1
                        if prompt:
                            answer = choose(f'{kind.upper()} replacement for {parent}',
                                            candidates, multiple, set())
                            if answer is None:
                                raise PropagationError('Replacement selection cancelled.')
                            answer = set(answer)
                            if (not answer or not answer <= set(candidates)
                                    or (not multiple and len(answer) != 1)):
                                raise PropagationError('Invalid replacement selection.')
                        else:
                            answer = {candidates[0]}
                        for replacement in sorted(answer):
                            include(replacement, 'RemoveGroupRepair+')
                            # Browse all available routes, even if one is active.
                            # Original C is retained for accurate missing counts.
                            if choose_paths is not None:
                                paths_for(replacement, 'ReplacementPathRequest+')
                        repaired = True
                        break
                    if repaired:
                        break
                if repaired:
                    continue
            # IP- removes nodes still unreachable after replacement repair.
            for node in sorted((original - removals) - reached - {root}):
                remove(node, 'IP-')
            if before == (frozenset(additions), frozenset(removals)):
                break

        active = effective()
        validator.configuration = SimpleNamespace(active=active)
        valid, messages = validator.verify_configuration()
        if not valid:
            raise PropagationError('Final validation failed:\n' + '\n'.join(messages))
        engine.configuration.update(active)
        return True, trace + [
            'Added: ' + (', '.join(sorted(active - original)) or '(none)'),
            'Removed: ' + (', '.join(sorted(original - active)) or '(none)'),
            'PASS: propagation and final validation.', 'CONFIGURATION IS REALISABLE']
    except PropagationError as error:
        return False, trace + [str(error), 'ADAPTATION NOT APPLIED. Configuration unchanged.']
