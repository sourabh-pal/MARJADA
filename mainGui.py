import tkinter as tk
from tkinter import ttk, messagebox
from data import barebone_features



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
        
        
    # REFRESH DEPENDENT FEATURES

    def refresh_dependent_features(self):

        self.dependent_list.delete(0,tk.END)

        feature = (self.feature_combo.get())

        if not feature:
            return

        # Current active configuration
        #active = (self.configuration.active)
        inactive = (self.configuration.inactive)

        # Reconstruction
        dependent = (self.engine.reconstruct_addition(feature,inactive))
        print(dependent)
        
        # Sort the feature in the list according to its name
        for dep in sorted(dependent):
            self.dependent_list.insert(tk.END,dep)


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
            "AdaptableTeaStore",
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

            success, messages = (self.engine.add_feature(feature,dependent_features))

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
            barebone_features
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


