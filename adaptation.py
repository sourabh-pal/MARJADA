
# ADAPTATION ENGINE

from collections import deque

class AdaptationEngine:

    def __init__(self, feature_model, configuration):

        self.fm = feature_model
        self.configuration = configuration

    # FEATURE ADDITION

    def add_feature(self, feature, selected_dependent_features=None):

        messages = []

        # Check feature existence

        if feature not in self.fm.features:

            return (False,["FAIL: Feature does not exist " "in the feature model."])

        # Check whether feature is already in the active configuration

        if feature in self.configuration.active:

            return (False,["FAIL: Feature is already active."])

        # present active configuration
        old_active = set(self.configuration.active)

        # Reconstruction

        reconstructed_features = (self.reconstruct_addition(feature,old_active))

        if selected_dependent_features is None:

            selected_dependent_features = set()

        selected_dependent_features = set(
            selected_dependent_features
        )

        # ----------------------------------------------------
        # Check selected dependent features
        # ----------------------------------------------------

        if not selected_dependent_features.issubset(
            reconstructed_features
        ):

            return (
                False,
                [
                    "FAIL: Selected dependent feature set "
                    "is not consistent with the feature model."
                ]
            )

        dependent_features = (
            selected_dependent_features
        )

        # ----------------------------------------------------
        # Construct new configuration
        # ----------------------------------------------------

        new_active = (
            old_active
            | dependent_features
            | {feature}
        )

        messages.append(
            f"Requested addition: {feature}"
        )

        # ----------------------------------------------------
        # Show dependent features
        # ----------------------------------------------------

        if dependent_features:

            messages.append(
                "Dependent features reconstructed: "
                + ", ".join(
                    sorted(dependent_features)
                )
            )

        else:

            messages.append(
                "Dependent features reconstructed: None"
            )

        # ====================================================
        # STRUCTURAL VALIDATION
        # ====================================================

        structural_ok, structural_messages = (
            self.validate_structural(
                new_active
            )
        )

        messages.extend(
            structural_messages
        )

        if not structural_ok:

            return (
                False,
                messages
            )

        # ====================================================
        # CROSS-TREE VALIDATION
        # ====================================================

        cross_tree_ok, cross_tree_messages = (
            self.validate_cross_tree(
                new_active
            )
        )

        messages.extend(
            cross_tree_messages
        )

        if not cross_tree_ok:

            return (
                False,
                messages
            )

        # ====================================================
        # INVOCATION PATH VALIDATION
        # ====================================================

        path = self.find_invocation_path(
            new_active,
            feature
        )

        if path is None:

            messages.append(
                "FAIL: No invocation path exists "
                "from an active invocation feature "
                "to the added feature."
            )

            return (
                False,
                messages
            )

        messages.append(
            "PASS: Invocation-path validation."
        )

        messages.append(
            "Invocation path: "
            + self.format_path(path)
        )

        # ----------------------------------------------------
        # Accept configuration
        # ----------------------------------------------------

        self.configuration.update(
            new_active
        )

        messages.append(
            f"VALID: {feature} was added successfully."
        )

        return (
            True,
            messages
        )

    # ========================================================
    # FEATURE REMOVAL
    # ========================================================

    def remove_feature(
        self,
        feature
    ):

        messages = []

        # ----------------------------------------------------
        # Check existence
        # ----------------------------------------------------

        if feature not in self.fm.features:

            return (
                False,
                [
                    "FAIL: Feature does not exist "
                    "in the feature model."
                ]
            )

        # ----------------------------------------------------
        # Check current state
        # ----------------------------------------------------

        if feature not in self.configuration.active:

            return (
                False,
                [
                    "FAIL: Feature is not active."
                ]
            )

        # ----------------------------------------------------
        # Root cannot be removed
        # ----------------------------------------------------

        if feature == "TeaStore":

            return (
                False,
                [
                    "FAIL: Root feature TeaStore "
                    "cannot be removed."
                ]
            )

        old_active = set(
            self.configuration.active
        )

        # ----------------------------------------------------
        # Reconstruction
        # ----------------------------------------------------

        dependent_features = (
            self.reconstruct_removal(
                feature,
                old_active
            )
        )

        # ----------------------------------------------------
        # New configuration
        # ----------------------------------------------------

        new_active = (
            old_active
            - dependent_features
            - {feature}
        )

        messages.append(
            f"Requested removal: {feature}"
        )

        if dependent_features:

            messages.append(
                "Dependent features removed: "
                + ", ".join(
                    sorted(dependent_features)
                )
            )

        else:

            messages.append(
                "Dependent features removed: None"
            )

        # ====================================================
        # STRUCTURAL VALIDATION
        # ====================================================

        structural_ok, structural_messages = (
            self.validate_structural(
                new_active
            )
        )

        messages.extend(
            structural_messages
        )

        if not structural_ok:

            return (
                False,
                messages
            )

        # ====================================================
        # CROSS-TREE VALIDATION
        # ====================================================

        cross_tree_ok, cross_tree_messages = (
            self.validate_cross_tree(
                new_active
            )
        )

        messages.extend(
            cross_tree_messages
        )

        if not cross_tree_ok:

            return (
                False,
                messages
            )

        # ----------------------------------------------------
        # No invocation validation for removal
        # ----------------------------------------------------

        messages.append(
            "INFO: Invocation-path validation is "
            "not required for feature removal."
        )

        # ----------------------------------------------------
        # Accept configuration
        # ----------------------------------------------------

        self.configuration.update(
            new_active
        )

        messages.append(
            f"VALID: {feature} was removed successfully."
        )

        return (
            True,
            messages
        )

    
    # RECONSTRUCTION AFTER ADDITION
    # it will consider all the inactive feature
    # because the dependent feature are non deterministic.
    # So, the developer need to choose the dependent feature 
    # by themselves. If any dependent feature already active, it will
    # not show in the dependent list.

    def reconstruct_addition(self,feature,inactive):
        
        ChooseDependentFeature = inactive - {feature}
        
        return ChooseDependentFeature
       

        
    # ========================================================
    # RECONSTRUCTION AFTER REMOVAL
    # ========================================================

    def reconstruct_removal(
        self,
        feature,
        active
    ):

        dependent = set()

        changed = True

        while changed:

            changed = False

            current_active = (
                active
                - dependent
                - {feature}
            )

            # ------------------------------------------------
            # Cross-tree dependencies
            # ------------------------------------------------

            for source in current_active:

                required_features = (
                    self.fm.cross_tree[
                        "requires"
                    ].get(
                        source,
                        []
                    )
                )

                # If source requires the feature being removed,
                # source must also be removed.
                if feature in required_features:

                    if source not in dependent:

                        dependent.add(
                            source
                        )

                        changed = True

            # ------------------------------------------------
            # Structural descendants
            # ------------------------------------------------

            for parent in list(current_active):

                structural_children = []

                for relation_type in [
                    "mandatory",
                    "optional",
                    "xor",
                    "or"
                ]:

                    structural_children.extend(
                        self.fm.structural[
                            relation_type
                        ].get(
                            parent,
                            []
                        )
                    )

                for child in structural_children:

                    if (
                        child in current_active
                        and self.has_structural_ancestor(
                            child,
                            feature
                        )
                    ):

                        dependent.add(
                            child
                        )

                        changed = True

        return dependent

    # ========================================================
    # CHECK STRUCTURAL ANCESTOR
    # ========================================================

    def has_structural_ancestor(
        self,
        child,
        ancestor
    ):

        queue = deque(
            [ancestor]
        )

        visited = set()

        while queue:

            current = queue.popleft()

            if current in visited:
                continue

            visited.add(
                current
            )

            for relation_type in [
                "mandatory",
                "optional",
                "xor",
                "or"
            ]:

                children = (
                    self.fm.structural[
                        relation_type
                    ].get(
                        current,
                        []
                    )
                )

                if child in children:
                    return True

                queue.extend(
                    children
                )

        return False

    # ========================================================
    # GET STRUCTURAL PARENT
    # ========================================================

    def find_structural_parents(
        self,
        feature
    ):

        parents = []

        for relation_type in [
            "mandatory",
            "optional",
            "xor",
            "or"
        ]:

            relations = (
                self.fm.structural[
                    relation_type
                ]
            )

            for parent, children in relations.items():

                if feature in children:

                    parents.append(
                        parent
                    )

        return parents

    # ========================================================
    # STRUCTURAL VALIDATION
    # ========================================================

    def validate_structural(
        self,
        active
    ):

        messages = []

        # ----------------------------------------------------
        # Root validation
        # ----------------------------------------------------

        if "TeaStore" not in active:

            messages.append(
                "FAIL: Root feature TeaStore "
                "must be active."
            )

            return (
                False,
                messages
            )

        # ----------------------------------------------------
        # Child -> Parent validation
        # ----------------------------------------------------

        for feature in active:

            if feature == "TeaStore":
                continue

            parents = self.find_structural_parents(
                feature
            )

            # If feature has a structural parent,
            # at least one parent must be active.
            if parents:

                if not any(
                    parent in active
                    for parent in parents
                ):

                    messages.append(
                        f"FAIL: Structural parent of "
                        f"{feature} is inactive."
                    )

                    return (
                        False,
                        messages
                    )

        # ----------------------------------------------------
        # Mandatory validation
        # ----------------------------------------------------

        for (
            parent,
            children
        ) in self.fm.structural[
            "mandatory"
        ].items():

            if parent in active:

                for child in children:

                    if child not in active:

                        messages.append(
                            f"FAIL: Mandatory feature "
                            f"{child} is missing from "
                            f"active configuration."
                        )

                        return (
                            False,
                            messages
                        )

        # ----------------------------------------------------
        # XOR validation
        # ----------------------------------------------------

        for (
            parent,
            children
        ) in self.fm.structural[
            "xor"
        ].items():

            if parent in active:

                count = sum(
                    child in active
                    for child in children
                )

                if count != 1:

                    messages.append(
                        f"FAIL: XOR violation at {parent}. "
                        f"Exactly one of "
                        f"{children} must be active."
                    )

                    return (
                        False,
                        messages
                    )

        # ----------------------------------------------------
        # OR validation
        # ----------------------------------------------------

        for (
            parent,
            children
        ) in self.fm.structural[
            "or"
        ].items():

            if parent in active:

                count = sum(
                    child in active
                    for child in children
                )

                if count < 1:

                    messages.append(
                        f"FAIL: OR violation at {parent}. "
                        f"At least one child must be active."
                    )

                    return (
                        False,
                        messages
                    )

        messages.append(
            "PASS: Structural validation."
        )

        return (
            True,
            messages
        )

    # ========================================================
    # CROSS-TREE VALIDATION
    # ========================================================

    def validate_cross_tree(
        self,
        active
    ):

        messages = []

        for (
            source,
            targets
        ) in self.fm.cross_tree[
            "requires"
        ].items():

            if source in active:

                for target in targets:

                    if target not in active:

                        messages.append(
                            f"FAIL: {source} requires "
                            f"{target}."
                        )

                        return (
                            False,
                            messages
                        )

        messages.append(
            "PASS: Cross-tree validation."
        )

        return (
            True,
            messages
        )

    # ========================================================
    # INVOCATION FEATURES
    # ========================================================

    def find_invocation_features(
        self,
        active
    ):

        # For the current TeaStore example,
        # WebUI is the invocation feature.

        invocation_features = set()

        if "WebUI" in active:

            invocation_features.add(
                "WebUI"
            )

        return invocation_features

    # ========================================================
    # BUILD ACTIVE GRAPH
    # ========================================================

    def build_graph(
        self,
        active
    ):

        graph = {
            feature: []
            for feature in active
        }

        # ----------------------------------------------------
        # Structural relations
        # ----------------------------------------------------

        relation_groups = [
            (
                "mandatory",
                "mandatory"
            ),
            (
                "optional",
                "optional"
            ),
            (
                "xor",
                "XOR"
            ),
            (
                "or",
                "OR"
            )
        ]

        for (
            relation_type,
            relation_name
        ) in relation_groups:

            relations = (
                self.fm.structural[
                    relation_type
                ]
            )

            for (
                parent,
                children
            ) in relations.items():

                if parent not in active:
                    continue

                for child in children:

                    if child in active:

                        graph[parent].append(
                            (
                                child,
                                relation_name
                            )
                        )

        # ----------------------------------------------------
        # Requires relations
        # ----------------------------------------------------

        for (
            source,
            targets
        ) in self.fm.cross_tree[
            "requires"
        ].items():

            if source not in active:
                continue

            for target in targets:

                if target in active:

                    graph[source].append(
                        (
                            target,
                            "requires"
                        )
                    )

        return graph

    # ========================================================
    # FIND INVOCATION PATH
    # ========================================================

    def find_invocation_path(
        self,
        active,
        target
    ):

        invocation_features = (
            self.find_invocation_features(
                active
            )
        )

        graph = self.build_graph(
            active
        )

        queue = deque()

        visited = set()

        parent = {}

        # ----------------------------------------------------
        # Start BFS from invocation features
        # ----------------------------------------------------

        for invocation_feature in (
            invocation_features
        ):

            queue.append(
                invocation_feature
            )

            visited.add(
                invocation_feature
            )

            parent[
                invocation_feature
            ] = None

        # ----------------------------------------------------
        # BFS
        # ----------------------------------------------------

        while queue:

            current = queue.popleft()

            if current == target:
                break

            for (
                next_feature,
                relation
            ) in graph.get(
                current,
                []
            ):

                if next_feature not in visited:

                    visited.add(
                        next_feature
                    )

                    parent[
                        next_feature
                    ] = (
                        current,
                        relation
                    )

                    queue.append(
                        next_feature
                    )

        # ----------------------------------------------------
        # Target unreachable
        # ----------------------------------------------------

        if target not in visited:

            return None

        # ----------------------------------------------------
        # Reconstruct path
        # ----------------------------------------------------

        path = []

        current = target

        while current is not None:

            previous_info = (
                parent[current]
            )

            if previous_info is None:

                path.append(
                    (
                        current,
                        None
                    )
                )

                break

            previous, relation = (
                previous_info
            )

            path.append(
                (
                    current,
                    relation
                )
            )

            current = previous

        path.reverse()

        return path

    # ========================================================
    # FORMAT PATH
    # ========================================================

    def format_path(
        self,
        path
    ):

        if not path:

            return "No path"

        result = path[0][0]

        for i in range(
            1,
            len(path)
        ):

            feature = path[i][0]

            relation = path[i][1]

            result += (
                f" --{relation}--> "
                f"{feature}"
            )

        return result
