"""Transactional ADD for MARJADA. No GUI or configuration changes before commit."""
from collections import deque
from heapq import heappop, heappush
class Cancelled(Exception):
    pass
def automatic_add(engine, feature, choose, choose_paths=None):
    """choose(title, options, multiple, selected) -> set of options or None.
    Optional edges are traversed only to establish invocation reachability.
    This revision preserves that behavior; it does not auto-activate all optional
    descendants. Paths minimize inactive nodes first, then hop count. This is an
    interactive reconstructor, not a complete search over all valid configurations.
    Requires cycles terminate through visited sets; repeated reconstruction states
    abort the transaction. Excluded/rejected features remain blocked for this ADD.
    """
    old = set(engine.configuration.active)
    active = set(old)
    blocked = set()
    log = []
    fm = engine.fm
    roots = set(engine.invocation_features)
    protected = roots | {engine.root_feature, feature}
    structural = fm.structural
    def ask(title, options, multiple=False, selected=()):
        options = set(options)
        answer = choose(title, sorted(options), multiple, set(selected))
        if answer is None:
            raise Cancelled("ADD cancelled; original configuration retained.")
        answer = set(answer)
        if not answer or not answer <= options:
            raise Cancelled("Invalid choice; original configuration retained.")
        if not multiple and len(answer) != 1:
            raise Cancelled("Choose exactly one option.")
        return answer
    def include(features):
        features = set(features)
        conflict = features & blocked
        if conflict:
            raise Cancelled(
                "Chosen constraints require previously rejected features: "
                + ", ".join(sorted(conflict))
                + ". Retry ADD with different choices."
            )
        active.update(features)
    def graph(nodes):
        edges = {f: set() for f in nodes}
        for relation in ("mandatory", "optional", "xor", "or"):
            for parent, children in structural.get(relation, {}).items():
                if parent in nodes:
                    edges[parent].update(set(children) & nodes)
        for source, targets in fm.cross_tree.get("requires", {}).items():
            if source in nodes:
                edges[source].update(set(targets) & nodes)
        return edges
    def reachable(nodes):
        edges = graph(nodes)
        seen = roots & nodes
        queue = deque(sorted(seen))
        while queue:
            for target in sorted(edges[queue.popleft()] - seen):
                seen.add(target)
                queue.append(target)
        return seen
    def connect(target):
        # Prefer paths that need fewer inactive features, then fewer edges.
        # A shorter inactive XOR branch must not displace an existing active
        # invocation path merely because it has fewer hops.
        if target in reachable(active) and not (choose_paths is not None and target == feature):
            return

        forbidden = set(blocked)
        for parent, children in structural.get("xor", {}).items():
            children = set(children)
            forced = children & required_features
            if len(forced) > 1:
                raise Cancelled(
                    "Requested feature requires conflicting XOR dependencies: "
                    + ", ".join(sorted(forced))
                )
            if forced:
                forbidden.update(children - forced)

        edges = graph(set(fm.features) - forbidden)
        if choose_paths is not None:
            from invocation_paths import iter_invocation_paths
            baseline = old if target == feature else set(active)
            selected_paths = choose_paths(
                target, iter_invocation_paths(edges, roots, target),
                set(baseline), structural, fm.cross_tree
            )
            if selected_paths is None:
                raise Cancelled("Path selection cancelled; configuration unchanged.")
            selected_paths = [tuple(path) for path in selected_paths]
            if not selected_paths:
                raise Cancelled("Choose at least one invocation path.")
            path_features = set()
            for path in selected_paths:
                if (not path or path[0] not in roots or path[-1] != target
                        or len(set(path)) != len(path)
                        or any(node not in edges for node in path)
                        or any(b not in edges[a] for a, b in zip(path, path[1:]))):
                    raise Cancelled("Invalid invocation path selection.")
                path_features.update(path)
                log.append("Selected invocation path: " + " -> ".join(path))
            include(path_features)
            required_features.update(path_features)
            return
        distances = {f: (0, 0) for f in roots if f in edges}
        parents = {}
        queue = [(0, 0, f) for f in sorted(distances)]
        while queue:
            additions, hops, source = heappop(queue)
            if distances.get(source) != (additions, hops):
                continue
            for child in sorted(edges[source]):
                cost = (additions + int(child not in active), hops + 1)
                if child not in distances or cost < distances[child]:
                    distances[child] = cost
                    parents[child] = {source}
                    heappush(queue, (*cost, child))
                elif cost == distances[child]:
                    parents[child].add(source)

        if target not in distances:
            raise Cancelled(f"No available invocation path to {target}.")
        path = [target]
        while distances[path[-1]] != (0, 0):
            candidates = parents[path[-1]]
            previous = (
                next(iter(candidates)) if len(candidates) == 1 else
                next(iter(ask(
                    f"Choose predecessor on an equally preferred path to {path[-1]}",
                    candidates
                )))
            )
            path.append(previous)
        path.reverse()
        include(path)
        required_features.update(path)
        log.append("Invocation path: " + " -> ".join(path))

    def deactivate_features(features):
        removed = set(features)
        while True:
            before = set(removed)
            # Parent removed => all structural children removed.
            for relation in ("mandatory", "optional", "xor", "or"):
                for parent, children in structural.get(
                    relation, {}
                ).items():
                    if parent in removed:
                        removed.update(children)
            # Remove features that lose every active invocation path.
            remaining = active - removed
            unreachable = (
                remaining
                - reachable(remaining)
                - {engine.root_feature}
            )
            removed.update(unreachable)
            if removed == before:
                break
        conflict = removed & protected
        if conflict:
            raise Cancelled(
                "Choice would remove a protected feature: "
                + ", ".join(sorted(conflict))
            )
        actually_removed = active & removed
        active.difference_update(removed)
        # Prevent reconstruction from adding these features again.
        blocked.update(removed)
        if actually_removed:
            log.append(
                "Deactivated: "
                + ", ".join(sorted(actually_removed))
            )
    def conflicts():
        pairs = set()
        for source, targets in fm.cross_tree.get("excludes", {}).items():
            for target in targets:
                if source in active and target in active:
                    pairs.add(tuple(sorted({source, target})))
        return sorted(pairs)
    try:
        if feature not in fm.features:
            raise Cancelled(f"Unknown feature: {feature}")
        if feature in old:
            raise Cancelled(f"{feature} is already active.")
        if not roots or not roots <= old:
            raise Cancelled("Apply a nonempty selection of active invocation features first.")
        if not old <= fm.features or not protected <= fm.features:
            raise Cancelled("Configuration contains unknown features.")
        references = set()
        for relation in ("mandatory", "optional", "xor", "or"):
            for parent, children in structural.get(relation, {}).items():
                references.add(parent)
                references.update(children)
        for relation in ("requires", "excludes"):
            for source, targets in fm.cross_tree.get(relation, {}).items():
                references.add(source)
                references.update(targets)
        if not references <= fm.features:
            raise Cancelled("Feature model relations reference unknown features.")
        # The request and its necessary dependencies are decisions already made.
        # Do not ask the user to choose an incompatible XOR sibling again.
        required_features = {feature}

        def expand_required():
            while True:
                before = set(required_features)
                for relation in ("mandatory", "optional", "xor", "or"):
                    for parent, children in structural.get(relation, {}).items():
                        children = set(children)
                        if children & required_features:
                            required_features.add(parent)
                        if relation == "mandatory" and parent in required_features:
                            required_features.update(children)
                for source, targets in fm.cross_tree.get("requires", {}).items():
                    if source in required_features:
                        required_features.update(targets)
                if required_features == before:
                    break
            protected.update(required_features)

        expand_required()
        include({engine.root_feature, feature})
        connect(feature)
        seen_states = set()
        xor_decisions = set()
        branch_choices = set()
        for iteration in range(1000):
            state = (frozenset(active), frozenset(blocked), frozenset(xor_decisions), frozenset(branch_choices))
            if state in seen_states:
                raise Cancelled(
                    "Repeated reconstruction state detected; ADD stopped without changes. "
                    "Retry with different choices."
                )
            seen_states.add(state)
            # Path nodes, requested ancestors, mandatory children and requires
            # are committed; unselected XOR/OR children remain genuine choices.
            expand_required()
            include(required_features)

            # Monotonic closure of parents, mandatory children and requires.
            while True:
                before = set(active)
                for relation in ("mandatory", "optional", "xor", "or"):
                    for parent, children in structural.get(relation, {}).items():
                        children = set(children)
                        if children & active:
                            include({parent})
                        if relation == "mandatory" and parent in active:
                            include(children)
                for source, targets in fm.cross_tree.get("requires", {}).items():
                    if source in active:
                        include(targets)
                if before == active:
                    break
            # One decision per iteration; then propagate again.
            decision = False
            for relation in ("xor", "or"):
                for parent, children in structural.get(relation, {}).items():
                    if parent not in active:
                        continue
                    children = set(children)
                    selected = children & active
                    forced = children & required_features
                    # A manually chosen branch can lead into an already-active
                    # XOR parent. Review that next group instead of silently
                    # retaining its old child (e.g. FullPower -> PageInformation).
                    branch_targets = set().union(*(
                        set(fm.cross_tree.get("requires", {}).get(source, ()))
                        for source in branch_choices & active
                    )) if branch_choices & active else set()
                    has_downstream_dependencies = any(
                        fm.cross_tree.get("requires", {}).get(child)
                        or any(structural.get(kind, {}).get(child)
                               for kind in ("mandatory", "optional", "xor", "or"))
                        for child in children
                    )
                    review_downstream = (
                        relation == "xor" and parent in branch_targets
                        and parent not in xor_decisions and not forced
                        and has_downstream_dependencies
                    )
                    affected_multi_xor = (
                        relation == "xor" and len(children) > 2
                        and parent not in xor_decisions
                        and (bool(forced) or parent not in old or len(selected) != 1)
                    )
                    if (review_downstream or affected_multi_xor
                            or (relation == "xor" and len(selected) != 1) or not selected):
                        options = children - blocked
                        if not options:
                            raise Cancelled(f"No available {relation.upper()} child for {parent}.")
                        if relation == "xor":
                            if len(forced) > 1:
                                raise Cancelled(
                                    "Requested feature requires conflicting XOR children: "
                                    + ", ".join(sorted(forced))
                                )
                            if not forced <= options:
                                raise Cancelled("A required XOR dependency was removed.")
                            needs_user_choice = (
                                len(children) > 2 or review_downstream
                                or (not forced and len(selected) != 1 and len(options) > 1)
                            )
                            if needs_user_choice:
                                chosen = ask(
                                    f"XOR: {parent} has {len(children)} total children. "
                                    "Choose exactly one. Required by this request/path: "
                                    + (", ".join(sorted(forced)) or "(none)")
                                    + ". An incompatible choice cancels ADD.",
                                    options, False, forced or selected
                                )
                                xor_decisions.add(parent)
                                branch_choices.update(chosen)
                                if not forced <= chosen:
                                    raise Cancelled(
                                        "Choice conflicts with the requested feature/path; ADD cancelled."
                                    )
                            else:
                                # A fixed request/path or sole option needs no guess.
                                # Unresolved downstream binary groups prompt above.
                                chosen = forced or (selected if len(selected) == 1 else
                                                    {sorted(options)[0]})
                                log.append(
                                    f"Automatic XOR choice for {parent}: "
                                    + ", ".join(sorted(chosen))
                                )
                        else:
                            chosen = ask(
                                f"OR: choose children for {parent}.",
                                options, True, selected
                            )
                        removed = selected - chosen
                        if removed & protected:
                            raise Cancelled(
                                "Choice would remove the requested "
                                "feature, root or invocation feature."
                            )
                        include(chosen)
                        if removed:
                            deactivate_features(removed)
                        decision = True
                        break
                if decision:
                    break
            if decision:
                continue
            pairs = conflicts()
            if pairs:
                pair = set(pairs[0])
                if len(pair) == 1:
                    raise Cancelled("A feature excludes itself: " + next(iter(pair)))
                keep = ask(
                    "EXCLUDES: choose which feature to KEEP. The other will be "
                    "removed; all dependencies will be checked again.", pair
                )
                removed = pair - keep
                if removed & protected:
                    raise Cancelled(
                        "Choice would remove the requested "
                        "feature, root or invocation feature."
                    )
                deactivate_features(removed)
                continue
            missing_paths = active - reachable(active) - {engine.root_feature}
            if missing_paths:
                connect(sorted(missing_paths)[0])
                continue
            # Verify actual final state; do not rely on earlier closure passes.
            errors = []
            if not protected <= active:
                errors.append("A requested, root, invocation or required dependency feature is missing.")
            if not active <= fm.features:
                errors.append("Unknown active features.")
            for relation in ("mandatory", "optional", "xor", "or"):
                for parent, children in structural.get(relation, {}).items():
                    children = set(children)
                    selected = children & active
                    if selected and parent not in active:
                        errors.append(f"{relation}: active child without parent {parent}.")
                    if parent in active:
                        if relation == "mandatory" and not children <= active:
                            errors.append(f"Missing mandatory child of {parent}.")
                        if relation == "xor" and len(selected) != 1:
                            errors.append(f"Invalid XOR selection at {parent}.")
                        if relation == "or" and not selected:
                            errors.append(f"Missing OR child at {parent}.")
            for source, targets in fm.cross_tree.get("requires", {}).items():
                if source in active and not set(targets) <= active:
                    errors.append(f"Unsatisfied requires at {source}.")
            if conflicts():
                errors.append("Unresolved excludes conflict.")
            if active - reachable(active) - {engine.root_feature}:
                errors.append("Missing invocation paths.")
            if errors:
                raise Cancelled("Final validation failed: " + " ".join(errors))

            # No pending rule or reachability violations: commit once.
            engine.configuration.update(active)
            log.extend([
                "Added: " + (", ".join(sorted(active - old)) or "(none)"),
                "Removed: " + (", ".join(sorted(old - active)) or "(none)"),
                "PASS: Mandatory, optional, XOR, OR, requires, excludes and invocation paths.",
                "CONFIGURATION IS REALISABLE"
            ])
            return True, log
        raise Cancelled("Reconstruction limit reached; original configuration retained.")
    except Cancelled as error:
        return False, log + [str(error)]
