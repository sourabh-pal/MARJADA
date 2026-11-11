#Created by Sourabh Pal

from collections import deque
from itertools import combinations


class RemovalError(Exception):
    pass


class RemovalCancelled(RemovalError):
    pass


class SearchLimit(RemovalError):
    pass


def automatic_remove(engine, feature, choose):
    original = set(engine.configuration.active)
    root = engine.root_feature
    invocations = set(engine.invocation_features)
    fm = engine.fm
    relations = {
        kind: {p: set(cs) for p, cs in fm.structural.get(kind, {}).items()}
        for kind in ('mandatory', 'optional', 'xor', 'or')
    }
    requires = {s: set(ts) for s, ts in fm.cross_tree.get('requires', {}).items()}
    excludes = {s: set(ts) for s, ts in fm.cross_tree.get('excludes', {}).items()}
    children = {}
    for group in relations.values():
        for parent, targets in group.items():
            children.setdefault(parent, set()).update(targets)
    protected = {root} | invocations
    mandatory_root = {root}
    queue = [root]
    while queue:
        for child in relations['mandatory'].get(queue.pop(), set()):
            if child not in mandatory_root:
                mandatory_root.add(child)
                queue.append(child)
    protected |= mandatory_root
    budget = [20000]

    def reachable(active):
        seen = invocations & active
        queue = deque(sorted(seen))
        while queue:
            source = queue.popleft()
            targets = children.get(source, set()) | requires.get(source, set())
            for target in sorted((targets & active) - seen):
                seen.add(target)
                queue.append(target)
        return seen

    def spend():
        budget[0] -= 1
        if budget[0] < 0:
            raise SearchLimit('REMOVE search limit reached; no changes applied.')

    def solve(active, blocked, interactive, history, messages, decisions=None):
        active, blocked = set(active), set(blocked)
        messages = list(messages)
        decisions = set(decisions or ())
        history = set(history)
        while True:
            spend()
            state = (frozenset(active), frozenset(blocked), frozenset(decisions))
            if state in history:
                raise RemovalError('Repeated reconstruction state; no changes applied.')
            history.add(state)
            if blocked & protected:
                raise RemovalError('Cannot remove protected features: ' + ', '.join(sorted(blocked & protected)))
            active -= blocked
            if not protected <= active:
                raise RemovalError('Root, invocation or mandatory-root feature is missing.')

            # Removal propagates to structural descendants and sources whose
            # mandatory/requires dependency was explicitly removed.
            remove = set()
            for parent, targets in children.items():
                if parent in blocked:
                    remove |= targets - blocked
            for parent, targets in relations['mandatory'].items():
                if parent in active and targets & blocked:
                    remove.add(parent)
            for source, targets in requires.items():
                if source in active and targets & blocked:
                    remove.add(source)
            for parent, targets in children.items():
                if parent in blocked:
                    remove |= targets & active
            if remove:
                blocked |= remove
                continue

            # Newly activated replacements need ancestors, mandatory children,
            # and requires targets. Blocked dependencies are never reactivated.
            additions = set()
            for parent, targets in children.items():
                if targets & active and parent not in active:
                    additions.add(parent)
            for parent, targets in relations['mandatory'].items():
                if parent in active:
                    additions |= targets - active
            for source, targets in requires.items():
                if source in active:
                    additions |= targets - active
            if additions & blocked:
                raise RemovalError('Replacement requires removed features: ' + ', '.join(sorted(additions & blocked)))
            if additions:
                active |= additions
                continue

            # A replacement conflicting with an active feature is rejected;
            # try another XOR option rather than silently removing unrelated data.
            for source, targets in excludes.items():
                if source in active and targets & active:
                    raise RemovalError(f'Excludes conflict at {source}: ' + ', '.join(sorted(targets & active)))

            # Ask for affected groups, newly activated parents, and unresolved
            # XOR/OR groups. Decisions last only for this transaction/branch;
            # reactivation in a later REMOVE gets a fresh decision.
            if interactive:
                for kind in ('xor', 'or', 'optional'):
                    for parent, targets in sorted(relations[kind].items()):
                        key = (kind, parent)
                        options = targets - blocked
                        selected = targets & active
                        affected = bool(targets & blocked)
                        newly_activated = parent not in original
                        unresolved = kind in ('xor', 'or') and not selected
                        if (parent not in active or key in decisions
                                or len(options) < 2
                                or not (affected or newly_activated or unresolved)):
                            continue
                        labels = sorted(options)
                        none_label = '[Keep no optional children]'
                        if kind == 'optional':
                            while none_label in options:
                                none_label += ' '
                            labels.append(none_label)
                        answer = choose(
                            f'{kind.upper()}: choose children for {parent}. '
                            + ('Choose exactly one remaining child.' if kind == 'xor'
                               else 'Choose the remaining children to keep/activate.')
                            + (' Select the no-children option by itself to keep none.'
                               if kind == 'optional' else ''),
                            labels, kind != 'xor', selected
                        )
                        if answer is None:
                            raise RemovalCancelled('REMOVE cancelled; original configuration retained.')
                        chosen = set(answer)
                        if kind == 'optional' and none_label in chosen:
                            if chosen != {none_label}:
                                raise RemovalError('Choose no optional children OR feature names, not both.')
                            chosen = set()
                        elif not chosen:
                            raise RemovalError('Choose at least one child.')
                        if not chosen <= options or (kind == 'xor' and len(chosen) != 1):
                            raise RemovalError('Invalid replacement selection.')
                        decisions.add(key)
                        rejected = (selected - chosen)
                        return solve(
                            (active - rejected) | chosen, blocked | rejected,
                            True, history,
                            messages + [f'{kind.upper()} choice for {parent}: '
                                        + (', '.join(sorted(chosen)) or '(none)')],
                            decisions=decisions
                        )

            # Only groups without an active child need a decision.
            for kind in ('xor', 'or'):
                for parent, targets in sorted(relations[kind].items()):
                    if parent not in active:
                        continue
                    selected = targets & active
                    if kind == 'xor' and len(selected) > 1:
                        raise RemovalError(f'Conflicting XOR children at {parent}.')
                    if selected:
                        continue
                    options = sorted(targets - blocked)
                    if not options:
                        # No replacement is possible: remove the parent unless
                        # protected, then reconstruct its ancestor groups.
                        return solve(active - {parent}, blocked | {parent}, interactive, history,
                                     messages + [f'Deactivated empty {kind.upper()} parent: {parent}'], decisions=decisions)
                    if kind == 'xor':
                        errors = []
                        for candidate in options:
                            try:
                                # Probe without user-facing dialogs. OR choices
                                # in a probe are explored until one valid set exists.
                                solve(active | {candidate}, blocked, False, history, messages, decisions=decisions)
                            except (SearchLimit, RemovalCancelled):
                                raise
                            except RemovalError as error:
                                errors.append(f'{candidate}: {error}')
                                continue
                            return solve(active | {candidate}, blocked, interactive, history,
                                         messages + [f'Automatic XOR replacement for {parent}: {candidate}'], decisions=decisions)
                        raise RemovalError(f'No valid XOR replacement for {parent}. ' + ' | '.join(errors))
                    if interactive:
                        answer = choose(
                            f'OR: {parent} needs at least one child. Choose replacements.',
                            options, True, set()
                        )
                        if answer is None:
                            raise RemovalCancelled('REMOVE cancelled; original configuration retained.')
                        chosen = set(answer)
                        if not chosen or not chosen <= set(options):
                            raise RemovalError('Invalid OR selection; no changes applied.')
                        return solve(active | chosen, blocked, True, history,
                                     messages + [f'OR replacement for {parent}: ' + ', '.join(sorted(chosen))], decisions=decisions)
                    # A dry feasibility probe may need multiple OR children.
                    
                    for count in range(1, len(options) + 1):
                        for choice in combinations(options, count):
                            try:
                                return solve(active | set(choice), blocked, False, history, messages, decisions=decisions)
                            except (SearchLimit, RemovalCancelled):
                                raise
                            except RemovalError:
                                continue
                    raise RemovalError(f'No valid OR replacement for {parent}.')

            # Repair XOR/OR first, so temporary loss of reachability does not
            # discard features that the replacement will reconnect.
            disconnected = active - reachable(active) - {root}
            if disconnected:
                blocked |= disconnected
                messages.append('Deactivated (unreachable): ' + ', '.join(sorted(disconnected)))
                continue

            # User policy: remove a nonprotected parent that lost its last child.
            # Leaves are untouched; root/invocation/mandatory-root parents stay.
            empty = {
                p for p, targets in children.items()
                if p in active and p not in protected
                and targets & blocked and not targets & active
            }
            if empty:
                blocked |= empty
                messages.append('Deactivated empty parents: ' + ', '.join(sorted(empty)))
                continue

            # Independent final invariant checks.
            if feature in active or not protected <= active:
                raise RemovalError('Final protection/removal validation failed.')
            for kind, group in relations.items():
                for parent, targets in group.items():
                    selected = targets & active
                    if selected and parent not in active:
                        raise RemovalError(f'Active child without parent {parent}.')
                    if parent not in active:
                        continue
                    if kind == 'mandatory' and not targets <= active:
                        raise RemovalError(f'Missing mandatory child at {parent}.')
                    if kind == 'xor' and len(selected) != 1:
                        raise RemovalError(f'Invalid XOR at {parent}.')
                    if kind == 'or' and not selected:
                        raise RemovalError(f'Invalid OR at {parent}.')
            for source, targets in requires.items():
                if source in active and not targets <= active:
                    raise RemovalError(f'Unsatisfied requires at {source}.')
            return active, messages

    try:
        if feature not in fm.features or feature not in original:
            raise RemovalError('Choose an active feature to remove.')
        if feature in protected:
            raise RemovalError('Cannot remove root, invocation or a feature transitively mandatory from root: ' + feature)
        if not invocations or not invocations <= original:
            raise RemovalError('Apply a nonempty selection of active invocation features first.')
        if not original <= fm.features or not protected <= fm.features:
            raise RemovalError('Unknown features in configuration or protected set.')
        referenced = set()
        for group in [*relations.values(), requires, excludes]:
            for source, targets in group.items():
                referenced.add(source)
                referenced |= targets
        if not referenced <= fm.features:
            raise RemovalError('Feature model relations reference unknown features.')
        result, messages = solve(original - {feature}, {feature}, True, set(), [])
        engine.configuration.update(result)
        return True, [f'Requested removal: {feature}'] + messages + [
            'Removed: ' + (', '.join(sorted(original - result)) or '(none)'),
            'Activated replacements: ' + (', '.join(sorted(result - original)) or '(none)'),
            'PASS: structural, requires, excludes and invocation validation.',
            'CONFIGURATION IS REALISABLE'
        ]
    except RemovalError as error:
        return False, [str(error), 'REMOVE not applied. Configuration unchanged.']
