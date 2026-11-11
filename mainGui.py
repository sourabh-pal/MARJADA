#Created by Sourabh Pal
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import types
import os
from model import FeatureModel
from config import Configuration
from adaptation import AdaptationEngine
from automatic_add import automatic_add
from automatic_remove import automatic_remove
# GUI
class MARJADAGUI:
    def __init__(self, root):
        self.root = root
        # The feature model is loaded through File -> Open Feature Model.
        self.fm = None
        self.configuration = None
        self.engine = None
        self.root_feature = None
        self.invocation_features = set()
        self.barebone_features = set()
        self.data_file = None
        self.root.title("MARJADA - Feature Adaptation and Reconstruction")
        self.root.geometry("1400x800")
        self.root.minsize(1100, 650)
        self.create_menu()
        self.create_styles()
        self.create_layout()
        self.show_empty_state()
    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Open Feature Model...",
            command=self.open_feature_model
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        #help_menu = tk.Menu(menubar, tearoff=0)
        #help_menu.add_command(
        #    label="About MARJADA",
        #    command=lambda: messagebox.showinfo(
        #        "About MARJADA",
        #        "Model-based Adaptive Reconstruction for "
        #        "Just-in-time Activation and Deactivation"
        #    )
        #)
        #menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
    def open_feature_model(self):
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="Select a feature-model data file",
            filetypes=[
                ("Feature model data files", "*.py *.txt"),
                ("Python files", "*.py"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return
        try:
            # The selected file must define root_feature,
            # invocation_features, feature_model and barebone_features.
            with open(file_path, "r", encoding="utf-8") as source_file:
                source = source_file.read()
            module = types.ModuleType("selected_feature_model")
            exec(compile(source, file_path, "exec"), module.__dict__)
            required = (
                "root_feature",
                "feature_model",
                "barebone_features"
            )
            missing = [name for name in required if not hasattr(module, name)]
            if missing:
                raise ValueError(
                    "The selected file is missing: " + ", ".join(missing)
                )
            new_fm = FeatureModel(module.feature_model)
            new_configuration = Configuration(new_fm, module.barebone_features)
            new_engine = AdaptationEngine(
                new_fm,
                new_configuration,
                module.root_feature,
                set()
            )
            # Replace the current model only after successful loading.
            self.fm = new_fm
            self.configuration = new_configuration
            self.engine = new_engine
            self.root_feature = module.root_feature
            #self.invocation_features = set(module.invocation_features)
            self.invocation_features = set()
            self.barebone_features = set(module.barebone_features)
            self.data_file = file_path
            self.root.title(
                "MARJADA - " + os.path.basename(file_path)
            )
            self.refresh_all()
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(
                tk.END,
                "Feature model loaded successfully.\\\n"
                f"File: {file_path}\\\n"
                f"Features: {len(self.fm.features)}\\\n"
            )
        except Exception as error:
            messagebox.showerror(
                "Feature Model Load Error",
                f"Could not load the selected file.\\\n\\\n{error}"
            )
    def show_empty_state(self):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(
            tk.END,
            "No feature model loaded.\\\n"
            "Select File → Open Feature Model... to load a data file."
        )
    # STYLES
    def create_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Title.TLabel",
            font=("Arial", 22, "bold")
            )
        style.configure(
            "Section.TLabel",
            font=("Arial", 13, "bold")
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
        adaptation_header = ttk.Frame(right)
        adaptation_header.pack(fill=tk.X)
        ttk.Label(
            adaptation_header,
            text="Adaptation Request",
            style="Section.TLabel"
        ).pack(side=tk.LEFT)
        self.invocation_button = ttk.Button(
            adaptation_header,
            text="Invocation Features",
            command=self.open_invocation_dropdown
        )
        self.invocation_button.pack(
            side=tk.LEFT,
            padx=(85, 0)
        )
        self.invocation_popup = None
        request_frame = ttk.Frame(
            right
        )
        request_frame.pack(
            fill=tk.X,
            pady=20
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
        # Switching operation refreshes the selectable active/inactive features.
        self.operation.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_feature_combo()
        )

        # Apply button
        self.apply_button = ttk.Button(right,
                                       text="Apply Adaptation",
                                       command=self.apply_adaptation)
        self.apply_button.pack(fill=tk.X,
                               pady=5)
        # Verification result
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
        # BOTTOM BUTTONS
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
            text="Verify Configuration",
            command=self.verify_current_configuration
        ).pack(
            side=tk.LEFT
        )
        #ttk.Button(
        #    bottom,
        #    text="Exit",
        #    command=self.root.destroy
        #).pack(
        #    side=tk.RIGHT
        #)
        # Operation change event
        self.operation.bind(
            "<<ComboboxSelected>>",
            lambda event:
                self.refresh_feature_combo()
        )
    def verify_current_configuration(self):
        if self.engine is None or self.configuration is None:
            messagebox.showwarning(
                "No Feature Model",
                "Load a feature model first.",
                parent=self.root
            )
            return
        # Use only the selection committed through Apply.
        self.engine.invocation_features = set(
            self.invocation_features
        )
        valid, messages = self.engine.verify_configuration()
        status = (
            "REALISABLE"
            if valid
            else "NOT REALISABLE"
        )
        report = (
            f"CURRENT CONFIGURATION: {status}\n\n"
            + "\n".join(messages)
        )
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, report)
    def close_invocation_dropdown(self):
        popup = self.invocation_popup
        if popup is not None and popup.winfo_exists():
            popup.destroy()
        self.invocation_popup = None
    def refresh_invocation_selection(self):
        """Keep invocation features limited to active features."""
        if self.configuration is None or self.engine is None:
            self.invocation_features = set()
            self.invocation_button.configure(
                text="Invocation Features ▼",
                state="disabled"
            )
            return
        self.invocation_features.intersection_update(
            self.configuration.active
        )
        self.engine.invocation_features = set(
            self.invocation_features
        )
        self.invocation_button.configure(
            text=(
                f"Invocation Features "
                f"({len(self.invocation_features)}) ▼"
            ),
            state="normal"
        )
    def open_invocation_dropdown(self):
        if self.configuration is None or self.engine is None:
            messagebox.showwarning(
                "No Feature Model",
                "Load a feature model first.",
                parent=self.root
            )
            return
        # Clicking the button again closes the dropdown.
        if (
            self.invocation_popup is not None
            and self.invocation_popup.winfo_exists()
        ):
            self.close_invocation_dropdown()
            return
        active_features = sorted(self.configuration.active)
        popup = tk.Toplevel(self.root)
        self.invocation_popup = popup
        popup.withdraw()
        popup.overrideredirect(True)
        popup.transient(self.root)
        frame = ttk.Frame(
            popup,
            padding=10,
            relief="solid",
            borderwidth=1
        )
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text="Choose active invocation features:"
        ).pack(anchor="w", pady=(0, 8))
        # Scrollable checkbox list.
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(
            list_frame,
            width=280,
            height=min(260, max(60, len(active_features) * 28)),
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        choices_frame = ttk.Frame(canvas)
        window_id = canvas.create_window(
            (0, 0),
            window=choices_frame,
            anchor="nw"
        )
        choices_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                window_id,
                width=event.width
            )
        )
        # These are draft choices until Apply is pressed.
        variables = {}
        for feature in active_features:
            variable = tk.BooleanVar(
                master=popup,
                value=feature in self.invocation_features
            )
            variables[feature] = variable
            ttk.Checkbutton(
                choices_frame,
                text=feature,
                variable=variable
            ).pack(anchor="w", padx=4, pady=3)
        def apply_selection():
            selected = {
                feature
                for feature, variable in variables.items()
                if variable.get()
            }
            # Recheck against the current active configuration.
            selected.intersection_update(
                self.configuration.active
            )
            if not selected:
                messagebox.showwarning(
                    "Invocation Features",
                    "Choose at least one active feature.",
                    parent=popup
                )
                return
            self.invocation_features = set(selected)
            self.engine.invocation_features = set(selected)
            self.refresh_invocation_selection()
            self.close_invocation_dropdown()
        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(
            buttons,
            text="Cancel",
            command=self.close_invocation_dropdown
        ).pack(side=tk.RIGHT)
        ttk.Button(
            buttons,
            text="Apply",
            command=apply_selection
        ).pack(side=tk.RIGHT, padx=(0, 8))
        popup.bind(
            "<Escape>",
            lambda event: self.close_invocation_dropdown()
        )
        popup.update_idletasks()
        x = self.invocation_button.winfo_rootx()
        y = (
            self.invocation_button.winfo_rooty()
            + self.invocation_button.winfo_height()
        )
        # Keep the dropdown within the screen.
        x = max(
            0,
            min(x, popup.winfo_screenwidth() - popup.winfo_reqwidth())
        )
        y = max(
            0,
            min(y, popup.winfo_screenheight() - popup.winfo_reqheight())
        )
        popup.geometry(f"+{x}+{y}")
        popup.deiconify()
        popup.focus_set()
    # REFRESH EVERYTHING
    def refresh_all(self):
        self.close_invocation_dropdown()
        if self.fm is None or self.configuration is None:
            self.active_list.delete(0, tk.END)
            self.inactive_list.delete(0, tk.END)
            self.feature_combo["values"] = []
            self.feature_combo.set("No model loaded")
            self.refresh_invocation_selection()
            self.refresh_tree()
            return
        # Read the configuration updated by ADD/REMOVE.
        self.refresh_configuration()
        # REMOVE shows active features; ADD shows inactive features.
        self.refresh_feature_combo()
        self.refresh_invocation_selection()
        # Rebuild feature tree with current active/inactive states.
        self.refresh_tree()
        self.root.update_idletasks()
    # REFRESH CONFIGURATION
    def refresh_configuration(self):
        # Active
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
        # Inactive
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
    # REFRESH FEATURE COMBOBOX
    def refresh_feature_combo(self):
        if self.configuration is None:
            self.feature_combo["values"] = []
            self.feature_combo.set("No model loaded")
            return

        if self.operation.get() == "ADD":
            values = sorted(self.configuration.inactive)
        else:
            values = sorted(self.configuration.active)

        self.feature_combo["values"] = values
        self.feature_combo.set("Select Feature")

    # REFRESH FEATURE TREE
    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.fm is None or self.root_feature is None:
            return
        self.insert_feature(
            self.root_feature,
            None,
            "root"
        )
    # INSERT FEATURE
    def insert_feature(self, feature, parent_id, relation ):
        state = ("ACTIVE"
                 if feature in self.configuration.active
                 else "INACTIVE"
                 )
        node = self.tree.insert(
            parent_id or "",
            tk.END,
            text=feature,
            values=(relation, state),
            open=True)
        # Mandatory
        for child in self.fm_children("mandatory", feature):
            self.insert_relation(node, child, "mandatory")
        # Optional
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
        for child in self.fm_children("or", feature):
            self.insert_relation(node, child, "OR")
    # INSERT RELATION
    def insert_relation(self, parent_node, feature, relation):
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
        # Recursive children
        for (relation_key, relation_name) in [
            ("mandatory", "mandatory"),
            ("optional", "optional"),
            ("xor", "XOR"),
            ("or", "OR")
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
    # GET CHILDREN
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
        
    def choose_add_features(
        self,
        title,
        options,
        multiple,
        selected
    ):
        popup = tk.Toplevel(self.root)
        popup.title("Adaptation: Feature choice")
        popup.transient(self.root)
        popup.geometry("650x480")
        result = None
        ttk.Label(
            popup,
            text=title,
            wraplength=610
        ).pack(
            anchor="w",
            padx=15,
            pady=15
        )
        container = ttk.Frame(popup)
        container.pack(
            fill=tk.BOTH,
            expand=True,
            padx=15
        )
        canvas = tk.Canvas(
            container,
            highlightthickness=0
        )
        scroll = ttk.Scrollbar(
            container,
            command=canvas.yview
        )
        canvas.configure(
            yscrollcommand=scroll.set
        )
        scroll.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )
        canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )
        choices = ttk.Frame(canvas)
        item = canvas.create_window(
            (0, 0),
            window=choices,
            anchor="nw"
        )
        choices.bind(
            "<Configure>",
            lambda event: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                item,
                width=event.width
            )
        )
        variables = {}
        radio = tk.StringVar(
            master=popup,
            value=""
        )
        if not multiple and len(selected) == 1:
            radio.set(next(iter(selected)))
        for option in options:
            if multiple:
                variable = tk.BooleanVar(
                    master=popup,
                    value=option in selected
                )
                variables[option] = variable
                ttk.Checkbutton(
                    choices,
                    text=option,
                    variable=variable
                ).pack(
                    anchor="w",
                    pady=4
                )
            else:
                ttk.Radiobutton(
                    choices,
                    text=option,
                    variable=radio,
                    value=option
                ).pack(
                    anchor="w",
                    pady=4
                )
        def apply():
            nonlocal result
            if multiple:
                chosen = {
                    name
                    for name, value in variables.items()
                    if value.get()
                }
            else:
                chosen = (
                    {radio.get()}
                    if radio.get()
                    else set()
                )
            if not chosen:
                messagebox.showwarning(
                    "Selection required",
                    "Choose at least one option.",
                    parent=popup
                )
                return
            result = chosen
            popup.destroy()
        buttons = ttk.Frame(popup)
        buttons.pack(
            fill=tk.X,
            padx=15,
            pady=15
        )
        ttk.Button(
            buttons,
            text="Cancel",
            command=popup.destroy
        ).pack(side=tk.RIGHT)
        ttk.Button(
            buttons,
            text="Apply choice",
            command=apply
        ).pack(
            side=tk.RIGHT,
            padx=8
        )
        popup.bind(
            "<Escape>",
            lambda event: popup.destroy()
        )
        popup.grab_set()
        self.root.wait_window(popup)
        return result
    # ========================================================
    # APPLY ADAPTATION
    # ========================================================
    def apply_adaptation(self):
        if self.engine is None or self.configuration is None:
            messagebox.showwarning(
                "No Feature Model",
                "Load a feature model first."
            )
            return
        operation = self.operation.get()
        feature = self.feature_combo.get()
        if feature not in self.fm.features:
            messagebox.showwarning(
                "Feature required",
                "Choose a feature first."
            )
            return
        if operation == "ADD":
            self.engine.invocation_features = set(
                self.invocation_features
            )
            success, messages = automatic_add(
                self.engine,
                feature,
                self.choose_add_features
            )
        elif operation == "REMOVE":
            self.engine.invocation_features = set(
                self.invocation_features
            )
            success, messages = automatic_remove(
                self.engine,
                feature,
                self.choose_add_features
            )
        else:
            return
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(
            tk.END,
            "\n\n".join(messages)
        )
        if not success:
            self.result_text.insert(
                tk.END,
                "\n\nADAPTATION NOT APPLIED. "
                "Configuration unchanged.\n"
            )
        self.refresh_all()
    # ========================================================
    # RESET CONFIGURATION
    # ========================================================
    def reset_configuration(self):
        if self.configuration is None:
            return
        self.configuration.update(
            self.barebone_features
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
        if self.engine is None:
            messagebox.showwarning("No Feature Model", "Load a feature model first.")
            return
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
        if self.engine is None:
            messagebox.showwarning("No Feature Model", "Load a feature model first.")
            return
        active = (
            self.configuration.active
        )
        #invocation_features = (
        #    self.engine.find_invocation_features(
        #        active
        #    )
        #)
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
            self.invocation_features
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
        for feature in sorted(active):
            # Invocation feature itself
            # is not shown as py path to itself.
            if feature in self.invocation_features:
                continue
            path = (self.engine.find_invocation_path(active, feature))
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
