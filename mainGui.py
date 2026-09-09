from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox


# ============================================================
# 1. FEATURE MODEL
# ============================================================

feature_model = {

    "features": {
        "TeaStore",
        "WebUI",
        "Persistence",
        "ImageService",
        "PageCompilation",
        "PageInfo",
        "PageImages",
        "CompilationWithRecommendations",
        "Recommender",
        "LocalAuth",
        "AuthPageInfo",
        "LowPower",
        "FullPower",
        "LocalCache",
        "ImageProvider",
        "BasicPageInfo"
    },

    # --------------------------------------------------------
    # Structural relationships
    # --------------------------------------------------------

    "structural": {

        # Mandatory:
        # If parent is active, child must be active.
        "mandatory": {

            "TeaStore": [
                "WebUI",
                "Persistence",
                "ImageService",
                "PageCompilation"
            ],

            "PageCompilation": [
                "PageInfo",
                "PageImages"
            ]
        },

        # Optional:
        # If parent is active, child may be active or inactive.
        "optional": {

            "TeaStore": [
                "LocalAuth"
            ],

            "PageCompilation": [
                "CompilationWithRecommendations"
            ]
        },

        # XOR:
        # Exactly one child must be active when parent is active.
        "xor": {

            "Recommender": [
                "LowPower",
                "FullPower"
            ],

            "Persistence": [
                "LocalCache"
            ],

            "ImageService": [
                "ImageProvider"
            ]
        },

        # OR:
        # At least one child must be active when parent is active.
        "or": {

            "PageInfo": [
                "BasicPageInfo"
            ]
        }
    },

    # --------------------------------------------------------
    # Cross-tree constraints
    # --------------------------------------------------------

    "cross_tree": {

        "requires": {

            "WebUI": [
                "PageCompilation"
            ],

            "PageCompilation": [
                "ImageService"
            ],

            "CompilationWithRecommendations": [
                "Recommender",
                "Persistence",
                "ImageService"
            ],

            "Recommender": [
                "Persistence",
                "WebUI"
            ],

            "PageInfo": [
                "Persistence"
            ]
        }
    }
}


# ============================================================
# 2. FEATURE MODEL CLASS
# ============================================================

class FeatureModel:

    def __init__(self, feature_model):

        self.features = set(
            feature_model["features"]
        )

        self.structural = (
            feature_model["structural"]
        )

        self.cross_tree = (
            feature_model["cross_tree"]
        )


# ============================================================
# 3. CONFIGURATION CLASS
# ============================================================

class Configuration:

    def __init__(
        self,
        feature_model,
        active_features
    ):

        self.feature_model = feature_model

        self.active = set(
            active_features
        )

        self.inactive = (
            self.feature_model.features
            - self.active
        )

    # --------------------------------------------------------
    # Update configuration
    # --------------------------------------------------------

    def update(self, active_features):

        self.active = set(
            active_features
        )

        self.inactive = (
            self.feature_model.features
            - self.active
        )


# ============================================================
# 4. ADAPTATION ENGINE
# ============================================================

class AdaptationEngine:

    def __init__(
        self,
        feature_model,
        configuration
    ):

        self.fm = feature_model
        self.configuration = configuration

    # ========================================================
    # FEATURE ADDITION
    # ========================================================

    def add_feature(
        self,
        feature,
        selected_dependent_features=None
    ):

        messages = []

        # ----------------------------------------------------
        # Check feature existence
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

        if feature in self.configuration.active:

            return (
                False,
                [
                    "FAIL: Feature is already active."
                ]
            )

        old_active = set(
            self.configuration.active
        )

        # ----------------------------------------------------
        # Reconstruction
        # ----------------------------------------------------

        reconstructed_features = (
            self.reconstruct_addition(
                feature,
                old_active
            )
        )

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

    # ========================================================
    # RECONSTRUCTION AFTER ADDITION
    # ========================================================

    def reconstruct_addition(
        self,
        feature,
        active
    ):

        dependent = set()

        queue = deque(
            [feature]
        )

        visited = set()

        while queue:

            current = queue.popleft()

            if current in visited:
                continue

            visited.add(
                current
            )

            # ------------------------------------------------
            # Mandatory children
            # ------------------------------------------------

            mandatory_children = (
                self.fm.structural[
                    "mandatory"
                ].get(
                    current,
                    []
                )
            )

            for child in mandatory_children:

                if (
                    child not in active
                    and child not in dependent
                ):

                    dependent.add(
                        child
                    )

                    queue.append(
                        child
                    )

            # ------------------------------------------------
            # XOR
            # ------------------------------------------------

            xor_children = (
                self.fm.structural[
                    "xor"
                ].get(
                    current,
                    []
                )
            )

            if xor_children:

                active_children = [
                    child
                    for child in xor_children
                    if child in active
                ]

                # If no XOR child is active,
                # select one deterministically.
                if not active_children:

                    selected = sorted(
                        xor_children
                    )[0]

                    if selected not in dependent:

                        dependent.add(
                            selected
                        )

                        queue.append(
                            selected
                        )

            # ------------------------------------------------
            # OR
            # ------------------------------------------------

            or_children = (
                self.fm.structural[
                    "or"
                ].get(
                    current,
                    []
                )
            )

            if or_children:

                active_children = [
                    child
                    for child in or_children
                    if child in active
                ]

                # If no OR child is active,
                # select one deterministically.
                if not active_children:

                    selected = sorted(
                        or_children
                    )[0]

                    if selected not in dependent:

                        dependent.add(
                            selected
                        )

                        queue.append(
                            selected
                        )

            # ------------------------------------------------
            # Requires
            # ------------------------------------------------

            required_features = (
                self.fm.cross_tree[
                    "requires"
                ].get(
                    current,
                    []
                )
            )

            for required in required_features:

                if (
                    required not in active
                    and required not in dependent
                ):

                    dependent.add(
                        required
                    )

                    queue.append(
                        required
                    )

        return dependent

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

            # If feature has py structural parent,
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


# ============================================================
# 5. INITIAL CONFIGURATION
# ============================================================

fm = FeatureModel(
    feature_model
)


# This initial configuration satisfies:
#
# TeaStore
# ├── WebUI
# ├── Persistence
# │   └── LocalCache       (XOR)
# ├── ImageService
# │   └── ImageProvider    (XOR)
# └── PageCompilation
#     ├── PageInfo
#     │   └── BasicPageInfo (OR)
#     └── PageImages
#
# Optional features:
# - LocalAuth = OFF
# - CompilationWithRecommendations = OFF
# - Recommender = OFF

initial_active = {

    "TeaStore",

    "WebUI",

    "Persistence",
    "LocalCache",

    "ImageService",
    "ImageProvider",

    "PageCompilation",

    "PageInfo",
    "BasicPageInfo",

    "PageImages"
}


configuration = Configuration(
    fm,
    initial_active
)


# ============================================================
# 6. ADAPTATION ENGINE
# ============================================================

engine = AdaptationEngine(
    fm,
    configuration
)


# ============================================================
# 7. GUI
# ============================================================

class MARJADAGUI:

    def __init__(
        self,
        root,
        fm,
        configuration,
        engine
    ):

        self.root = root

        # IMPORTANT:
        # All GUI operations use these same objects.
        self.fm = fm
        self.configuration = configuration
        self.engine = engine

        self.root.title(
            "MARJADA - Feature Adaptation and Reconstruction"
        )

        self.root.geometry(
            "1400x800"
        )

        self.root.minsize(
            1100,
            650
        )

        self.create_styles()

        self.create_layout()

        self.refresh_all()

    # ========================================================
    # STYLES
    # ========================================================

    def create_styles(self):

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except tk.TclError:

            pass

        style.configure(
            "Title.TLabel",
            font=(
                "Arial",
                22,
                "bold"
            )
        )

        style.configure(
            "Section.TLabel",
            font=(
                "Arial",
                13,
                "bold"
            )
        )

    # ========================================================
    # REFRESH DEPENDENT FEATURES
    # ========================================================

    def refresh_dependent_features(self):

        self.dependent_list.delete(
            0,
            tk.END
        )

        feature = (
            self.feature_combo.get()
        )

        if not feature:

            return

        # Current active configuration
        active = (
            self.configuration.active
        )

        # Reconstruction
        dependent = (
            self.engine.reconstruct_addition(
                feature,
                active
            )
        )

        # Requested feature নিজে dependent নয়
        dependent.discard(
            feature
        )

        # Only inactive dependent features
        dependent = {
            f
            for f in dependent
            if f not in active
        }

        for dep in sorted(
            dependent
        ):

            self.dependent_list.insert(
                tk.END,
                dep
            )

        # Default select reconstructed dependencies
        if dependent:

            for index in range(
                self.dependent_list.size()
            ):

                self.dependent_list.selection_set(
                    index
                )

    # ========================================================
    # MAIN GUI LAYOUT
    # ========================================================

    def create_layout(self):

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = ttk.Label(
            self.root,
            text="MARJADA",
            style="Title.TLabel"
        )

        title.pack(
            pady=(10, 0)
        )

        subtitle = ttk.Label(
            self.root,
            text=(
                "Model-based Adaptive Reconstruction "
                "for Just-in-time Activation and Deactivation"
            )
        )

        subtitle.pack(
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # Main panel
        # ----------------------------------------------------

        main = ttk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL
        )

        main.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=5
        )

        # ====================================================
        # LEFT PANEL
        # ====================================================

        left = ttk.Frame(
            main
        )

        main.add(
            left,
            weight=3
        )

        model_label = ttk.Label(
            left,
            text="Feature Model",
            style="Section.TLabel"
        )

        model_label.pack(
            anchor="w",
            pady=(0, 5)
        )

        # ----------------------------------------------------
        # Feature tree
        # ----------------------------------------------------

        self.tree = ttk.Treeview(
            left,
            columns=(
                "relation",
                "state"
            ),
            show="tree headings"
        )

        self.tree.heading(
            "#0",
            text="Feature"
        )

        self.tree.heading(
            "relation",
            text="Relation"
        )

        self.tree.heading(
            "state",
            text="State"
        )

        self.tree.column(
            "#0",
            width=260
        )

        self.tree.column(
            "relation",
            width=120
        )

        self.tree.column(
            "state",
            width=100
        )

        tree_scroll = ttk.Scrollbar(
            left,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=tree_scroll.set
        )

        self.tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        tree_scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

        # ====================================================
        # MIDDLE PANEL
        # ====================================================

        middle = ttk.Frame(
            main
        )

        main.add(
            middle,
            weight=2
        )

        # ----------------------------------------------------
        # Active features
        # ----------------------------------------------------

        active_label = ttk.Label(
            middle,
            text="Active Configuration",
            style="Section.TLabel"
        )

        active_label.pack(
            anchor="w"
        )

        self.active_list = tk.Listbox(
            middle,
            height=15
        )

        self.active_list.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(5, 15)
        )

        # ----------------------------------------------------
        # Inactive features
        # ----------------------------------------------------

        inactive_label = ttk.Label(
            middle,
            text="Inactive Features",
            style="Section.TLabel"
        )

        inactive_label.pack(
            anchor="w"
        )

        self.inactive_list = tk.Listbox(
            middle,
            height=15
        )

        self.inactive_list.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(5, 10)
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right = ttk.Frame(
            main
        )

        main.add(
            right,
            weight=3
        )

        # ----------------------------------------------------
        # Adaptation request
        # ----------------------------------------------------

        adaptation_label = ttk.Label(
            right,
            text="Adaptation Request",
            style="Section.TLabel"
        )

        adaptation_label.pack(
            anchor="w"
        )

        request_frame = ttk.Frame(
            right
        )

        request_frame.pack(
            fill=tk.X,
            pady=10
        )

        # ----------------------------------------------------
        # Operation
        # ----------------------------------------------------

        ttk.Label(
            request_frame,
            text="Operation:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.operation = ttk.Combobox(
            request_frame,
            values=[
                "ADD",
                "REMOVE"
            ],
            state="readonly",
            width=12
        )

        self.operation.current(
            0
        )

        self.operation.grid(
            row=0,
            column=1,
            padx=8
        )

        # ----------------------------------------------------
        # Feature
        # ----------------------------------------------------

        ttk.Label(
            request_frame,
            text="Feature:"
        ).grid(
            row=0,
            column=2,
            sticky="w"
        )

        self.feature_combo = ttk.Combobox(
            request_frame,
            state="readonly",
            width=30
        )

        self.feature_combo.grid(
            row=0,
            column=3,
            padx=8
        )

        # ----------------------------------------------------
        # Dependent features
        # ----------------------------------------------------

        ttk.Label(
            request_frame,
            text="Dependent Features:"
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 5)
        )

        self.dependent_list = tk.Listbox(
            request_frame,
            selectmode=tk.MULTIPLE,
            height=7,
            width=35,
            exportselection=False
        )

        self.dependent_list.grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(0, 10)
        )

        self.feature_combo.bind(
            "<<ComboboxSelected>>",
            lambda event:
                self.refresh_dependent_features()
        )

        # ----------------------------------------------------
        # Apply button
        # ----------------------------------------------------

        self.apply_button = ttk.Button(
            right,
            text="Apply Adaptation",
            command=self.apply_adaptation
        )

        self.apply_button.pack(
            fill=tk.X,
            pady=5
        )

        # ----------------------------------------------------
        # Verification result
        # ----------------------------------------------------

        result_label = ttk.Label(
            right,
            text="Verification Result",
            style="Section.TLabel"
        )

        result_label.pack(
            anchor="w",
            pady=(15, 5)
        )

        self.result_text = tk.Text(
            right,
            height=20,
            wrap=tk.WORD,
            font=(
                "Courier New",
                10
            )
        )

        self.result_text.pack(
            fill=tk.BOTH,
            expand=True
        )

        # ====================================================
        # BOTTOM BUTTONS
        # ====================================================

        bottom = ttk.Frame(
            self.root
        )

        bottom.pack(
            fill=tk.X,
            padx=10,
            pady=10
        )

        ttk.Button(
            bottom,
            text="Reset Configuration",
            command=self.reset_configuration
        ).pack(
            side=tk.LEFT
        )

        ttk.Button(
            bottom,
            text="Show Active Graph",
            command=self.show_graph
        ).pack(
            side=tk.LEFT,
            padx=10
        )

        ttk.Button(
            bottom,
            text="Show Invocation Path",
            command=self.show_invocation_path
        ).pack(
            side=tk.LEFT
        )

        ttk.Button(
            bottom,
            text="Exit",
            command=self.root.destroy
        ).pack(
            side=tk.RIGHT
        )

        # ----------------------------------------------------
        # Operation change event
        # ----------------------------------------------------

        self.operation.bind(
            "<<ComboboxSelected>>",
            lambda event:
                self.refresh_feature_combo()
        )

    # ========================================================
    # REFRESH EVERYTHING
    # ========================================================

    def refresh_all(self):

        self.refresh_configuration()

        self.refresh_feature_combo()

        self.refresh_tree()

    # ========================================================
    # REFRESH CONFIGURATION
    # ========================================================

    def refresh_configuration(self):

        # ----------------------------------------------------
        # Active
        # ----------------------------------------------------

        self.active_list.delete(
            0,
            tk.END
        )

        for feature in sorted(
            self.configuration.active
        ):

            self.active_list.insert(
                tk.END,
                feature
            )

        # ----------------------------------------------------
        # Inactive
        # ----------------------------------------------------

        self.inactive_list.delete(
            0,
            tk.END
        )

        for feature in sorted(
            self.configuration.inactive
        ):

            self.inactive_list.insert(
                tk.END,
                feature
            )

    # ========================================================
    # REFRESH FEATURE COMBOBOX
    # ========================================================

    def refresh_feature_combo(self):

        operation = (
            self.operation.get()
        )

        if operation == "ADD":

            values = sorted(
                self.configuration.inactive
            )

        else:

            values = sorted(
                self.configuration.active
            )

        self.feature_combo["values"] = (
            values
        )

        if values:

            self.feature_combo.current(
                0
            )

        else:

            self.feature_combo.set(
                ""
            )

        # ADD হলে dependent features update
        if operation == "ADD":

            self.refresh_dependent_features()

        else:

            self.dependent_list.delete(
                0,
                tk.END
            )

    # ========================================================
    # REFRESH FEATURE TREE
    # ========================================================

    def refresh_tree(self):

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )

        self.insert_feature(
            "TeaStore",
            None,
            "root"
        )

    # ========================================================
    # INSERT FEATURE
    # ========================================================

    def insert_feature(
        self,
        feature,
        parent_id,
        relation
    ):

        state = (
            "ACTIVE"
            if feature in self.configuration.active
            else "INACTIVE"
        )

        node = self.tree.insert(
            parent_id or "",
            tk.END,
            text=feature,
            values=(
                relation,
                state
            ),
            open=True
        )

        # ----------------------------------------------------
        # Mandatory
        # ----------------------------------------------------

        for child in self.fm_children(
            "mandatory",
            feature
        ):

            self.insert_relation(
                node,
                child,
                "mandatory"
            )

        # ----------------------------------------------------
        # Optional
        # ----------------------------------------------------

        for child in self.fm_children(
            "optional",
            feature
        ):

            self.insert_relation(
                node,
                child,
                "optional"
            )

        # ----------------------------------------------------
        # XOR
        # ----------------------------------------------------

        for child in self.fm_children(
            "xor",
            feature
        ):

            self.insert_relation(
                node,
                child,
                "XOR"
            )

        # ----------------------------------------------------
        # OR
        # ----------------------------------------------------

        for child in self.fm_children(
            "or",
            feature
        ):

            self.insert_relation(
                node,
                child,
                "OR"
            )

    # ========================================================
    # INSERT RELATION
    # ========================================================

    def insert_relation(
        self,
        parent_node,
        feature,
        relation
    ):

        state = (
            "ACTIVE"
            if feature in self.configuration.active
            else "INACTIVE"
        )

        node = self.tree.insert(
            parent_node,
            tk.END,
            text=feature,
            values=(
                relation,
                state
            ),
            open=True
        )

        # ----------------------------------------------------
        # Recursive children
        # ----------------------------------------------------

        for (
            relation_key,
            relation_name
        ) in [

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

        ]:

            for child in self.fm_children(
                relation_key,
                feature
            ):

                self.insert_relation(
                    node,
                    child,
                    relation_name
                )

    # ========================================================
    # GET CHILDREN
    # ========================================================

    def fm_children(
        self,
        relation_type,
        feature
    ):

        return (
            self.fm.structural[
                relation_type
            ].get(
                feature,
                []
            )
        )

    # ========================================================
    # APPLY ADAPTATION
    # ========================================================

    def apply_adaptation(self):

        operation = (
            self.operation.get()
        )

        feature = (
            self.feature_combo.get()
        )

        # ----------------------------------------------------
        # Check feature
        # ----------------------------------------------------

        if not feature:

            messagebox.showwarning(
                "No Feature Selected",
                "Please select py feature."
            )

            return

        # ====================================================
        # ADD
        # ====================================================

        if operation == "ADD":

            # Get selected dependent features
            selected_indices = (
                self.dependent_list.curselection()
            )

            dependent_features = {

                self.dependent_list.get(i)

                for i in selected_indices

            }

            success, messages = (
                self.engine.add_feature(
                    feature,
                    dependent_features
                )
            )

        # ====================================================
        # REMOVE
        # ====================================================

        else:

            success, messages = (
                self.engine.remove_feature(
                    feature
                )
            )

        # ====================================================
        # SHOW RESULT
        # ====================================================

        self.result_text.delete(
            "1.0",
            tk.END
        )

        for message in messages:

            self.result_text.insert(
                tk.END,
                message + "\n\n"
            )

        self.result_text.insert(
            tk.END,
            "\n" + "=" * 45 + "\n"
        )

        if success:

            self.result_text.insert(
                tk.END,
                "CONFIGURATION IS VALID\n"
            )

        else:

            self.result_text.insert(
                tk.END,
                "CONFIGURATION IS INVALID\n"
            )

        self.result_text.insert(
            tk.END,
            "=" * 45 + "\n"
        )

        # IMPORTANT:
        # configuration change হওয়ার পরে
        # সব GUI element একই configuration object থেকে refresh হবে.

        self.refresh_all()

    # ========================================================
    # RESET CONFIGURATION
    # ========================================================

    def reset_configuration(self):

        self.configuration.update(
            initial_active
        )

        self.result_text.delete(
            "1.0",
            tk.END
        )

        self.result_text.insert(
            tk.END,
            "Configuration reset to initial state.\n"
        )

        self.refresh_all()

    # ========================================================
    # SHOW ACTIVE GRAPH
    # ========================================================

    def show_graph(self):

        active = (
            self.configuration.active
        )

        graph = (
            self.engine.build_graph(
                active
            )
        )

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Active Feature Graph"
        )

        window.geometry(
            "950x700"
        )

        text = tk.Text(
            window,
            wrap=tk.WORD,
            font=(
                "Courier New",
                11
            )
        )

        text.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        text.insert(
            tk.END,
            "ACTIVE FEATURE GRAPH\n"
        )

        text.insert(
            tk.END,
            "====================\n\n"
        )

        for source in sorted(
            graph
        ):

            if not graph[source]:
                continue

            text.insert(
                tk.END,
                f"{source}\n"
            )

            for (
                target,
                relation
            ) in graph[source]:

                text.insert(
                    tk.END,
                    f"    --{relation}--> "
                    f"{target}\n"
                )

            text.insert(
                tk.END,
                "\n"
            )

    # ========================================================
    # SHOW INVOCATION PATH
    # ========================================================

    def show_invocation_path(self):

        active = (
            self.configuration.active
        )

        invocation_features = (
            self.engine.find_invocation_features(
                active
            )
        )

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Invocation Paths"
        )

        window.geometry(
            "900x650"
        )

        text = tk.Text(
            window,
            wrap=tk.WORD,
            font=(
                "Courier New",
                11
            )
        )

        text.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        text.insert(
            tk.END,
            "INVOCATION FEATURES\n"
        )

        text.insert(
            tk.END,
            "===================\n\n"
        )

        for feature in sorted(
            invocation_features
        ):

            text.insert(
                tk.END,
                f"* {feature}\n"
            )

        text.insert(
            tk.END,
            "\n\nPATHS TO ACTIVE FEATURES\n"
        )

        text.insert(
            tk.END,
            "========================\n\n"
        )

        for feature in sorted(
            active
        ):

            # Invocation feature itself
            # is not shown as py path to itself.
            if feature in invocation_features:

                continue

            path = (
                self.engine.find_invocation_path(
                    active,
                    feature
                )
            )

            if path is None:

                text.insert(
                    tk.END,
                    f"{feature}\n"
                    f"    NO INVOCATION PATH\n\n"
                )

            else:

                text.insert(
                    tk.END,
                    f"{feature}\n"
                )

                text.insert(
                    tk.END,
                    "    "
                    + self.engine.format_path(
                        path
                    )
                    + "\n\n"
                )


# ============================================================
# 8. RUN GUI
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = MARJADAGUI(
        root,
        fm,
        configuration,
        engine
    )

    root.mainloop()