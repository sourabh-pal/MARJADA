
# ADAPTATION ENGINE

from collections import defaultdict, deque
from data import root_feature, invocation_features


#from numpy.distutils.conv_template import paren_repl

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

        if selected_dependent_features is None:

            selected_dependent_features = set()

        selected_dependent_features = set(
            selected_dependent_features)

    

        dependent_features = (selected_dependent_features)


        # Construct new configuration
        
        new_active = (old_active 
                      | dependent_features 
                      | {feature})

        messages.append(f"Requested addition: {feature}")

        
        # STRUCTURAL VALIDATION

        (structural_ok, structural_messages, new_active) = (
            self.validate_structural(feature, new_active))

        messages.extend(structural_messages)

        if not structural_ok:
            return (False,messages)


        # CROSS-TREE VALIDATION

        cross_tree_ok, cross_tree_messages = (
            self.validate_cross_tree(new_active))

        messages.extend(cross_tree_messages)

        if not cross_tree_ok:

            return (False, messages)


        # INVOCATION PATH VALIDATION

        (path, missing_feature) = self.find_invocation_path(new_active,
                                         feature, dependent_features)
        
        if path is None:

            messages.append(
                f"FAIL: No invocation path exists "
                f"from an active invocation feature "
                f"to the added feature. "
                f"Missing features: {missing_feature}."
                )

            return (False, messages)

        messages.append("PASS: Invocation-path validation.")

        # Accept configuration

        self.configuration.update(new_active)

        messages.append(
            f"VALID: {feature} was added successfully."
            )

        return (True, messages)
    

    # FEATURE REMOVAL
   
    def remove_feature(self, feature, 
                       selected_dependent_features=None):

        messages = []

        # Check existence
     
        #if feature not in self.fm.features:  
        #   return (False,
        #          [
        #             "FAIL: Feature does not exist "
        #            "in the feature model."
        #           ])

        # Check current state
     
        #if feature not in self.configuration.active:

        #   return (False,
        #            [
        #                "FAIL: Feature is not active."
        #                ])

        # Root cannot be removed
       
        if feature == root_feature:

            return (False,
                    [
                        "FAIL: Root feature AdaptableTeaStore "
                        "cannot be removed."
                        ])

        old_active = set(self.configuration.active)

        # Reconstruction
      
        #dependent_features = (self.reconstruct_removal(feature, old_active))
        
        dependent_features = (selected_dependent_features)

        
        # New configuration
        
        new_active = (old_active - dependent_features - {feature})

        messages.append(f"Requested removal: {feature}")

        if dependent_features:

            messages.append(
                "Dependent features removed: "
                + ", ".join(sorted(dependent_features))
                )

        else:

            messages.append("Dependent features removed: None")

        # STRUCTURAL VALIDATION

        (structural_ok, structural_messages, new_active) = (
            self.validate_structural(feature, new_active))

        messages.extend(structural_messages)

        if not structural_ok:

            return (False, messages)

        # CROSS-TREE VALIDATION

        cross_tree_ok, cross_tree_messages = (
            self.validate_cross_tree(new_active))

        messages.extend(cross_tree_messages)

        if not cross_tree_ok:

            return (False, messages)


        
        # INVOCATION PATH VALIDATION
        
        dependent_feature_to_remove = self.analyse_removal(
            new_active,invocation_features)
        
        if dependent_feature_to_remove:
            
            messages.append(
                f"FAIL: No invocation path exists "
                f"from an active invocation feature "
                f"to these feature. "
                f"These features should choose "
                f"as dependent feature: {dependent_feature_to_remove}."
                )
            
            return (False, messages)
        
        messages.append("PASS: Invocation-path validation.")

         
        # ----------------------------------------------------
        # Accept configuration
        # ----------------------------------------------------

        self.configuration.update(new_active)

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

    def reconstruct_addition(self, feature, inactive):
        
        ChooseDependentFeatureAdd = inactive - {feature}
        
        return ChooseDependentFeatureAdd
    
    
    
    def reconstruct_deletion(self, feature, active):
        
        ChooseDependentFeatureDel = active - {feature}
        
        return ChooseDependentFeatureDel
       

        
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

    
    
    # It need to check that the feature we are adding 
    # is reachable from the root feature.
    # So, there should be direct and continuous path from
    # the root feature to the feature is going to be added.
    def find_feature_path(self, feature):
        
        featuresInPath = set()
        
        flag_feature = feature
        featuresInPath.add(feature)
        
        while flag_feature != root_feature:
            
            parent_found = False
            
            for relation_types in ["mandatory", "optional", 
                                   "xor", "or"]:
            
                relations = (self.fm.structural[relation_types])
            
                for parent, children in relations.items():
                
                    for child in children:
                    
                        if child == flag_feature:
                            featuresInPath.add(parent)
                            flag_feature = parent
                            parent_found = True
                            break
                
                if parent_found:
                    break
        
        return featuresInPath


    # STRUCTURAL VALIDATION

    def validate_structural(self, feature, active):

        messages = []

        # Root validation

        if root_feature not in active:
            messages.append(
                "FAIL: Root feature AdaptableTeaStore "
                "must be active.")

            return (False,messages, active)
        
        

        # MANDATORY VALIDATION:
        # Two types of mandatory validation
        # 1. if parent is active the child must be active
        for (parent,children) in self.fm.structural[
            "mandatory"].items():

            if parent in active:

                for child in children:

                    if child not in active:

                        messages.append(
                            f"FAIL: Mandatory feature "
                            f"{child} is missing from "
                            f"active configuration."
                        )

                        return (False, messages, active)
                    
            # 2. if child is active then parent must be active    
            for child in children:
                
                if child in active:
                    
                    if parent not in active:
                        
                        messages.append(
                            f"FAIL: Mandatory feature "
                            f"{parent} is missing from "
                            f"active configuration."
                            )
                        
                        return(False, messages, active)
                        

        
        # XOR VALIDATION
        
        for (parent,children) in self.fm.structural["xor"].items():

            # if parent is active then exactly one child must be active
            if parent in active:
                
                child_list = set()
                
                count = 0
                
                for child in children:
                    
                    if child in active:
                        
                        child_list.add(child)
                        
                        count = count + 1

                if count != 1:
                    
                    if feature in child_list:
                    
                        active = active - child_list
                        
                        active.add(feature)
                        
                    else:
                        
                        messages.append(
                            f"FAIL: XOR violation at {parent}. "
                            f"Exactly one of "
                            f"{children} must be active."
                            )

                        return (False,messages, active)
            
            # if exactly one children is active then 
            # parent must be active
            else:
                count = 0
                for child in children:
                    if child in active:
                        count = count + 1
                
                # if one or more children active but
                # the parent is inactive
                if count >= 1:
                    if parent not in active:
                        
                        messages.append(
                        f"FAIL: XOR violation at {children}. "
                        f"The {parent} must be active. "
                        f"Exactly one {children} must be active. "
                        )
                        return (False,messages, active)
                
                    
        # OR VALIDATION
    
        for (parent, children) in self.fm.structural["or"].items():

            if parent in active:
                
                count = sum(child in active for child in children)

                if count < 1:

                    messages.append(
                        f"FAIL: OR violation at {parent}. "
                        f"At least one child must be active."
                        )

                    return (False, messages, active)
                
            elif parent not in active:
                
                count = sum(child in active for child in children)
                
                if count > 0:
                    
                    messages.append(
                        f"FAIL: OR violation at {children}. "
                        f"The {parent} must be active."
                        )
        
        
       
        # Check whether the Functional Path exist
        # from the root feature to the activating feature.
        # In case, there is inconsistent with the functional
        # path, then the inactive feature in the path
        # must be add as a dependent feature by the developer.
        for feature in active:
            
            if feature == root_feature:
                continue
            
            ParentPath = self.find_feature_path(feature)
            ParentPath.add(feature)
            
            if not ParentPath.issubset(active):
                
                messages.append(
                    f"FAIL: The Functional Path {ParentPath} is "
                    f"inconsistent with to activate the feature."
                    )
                return (False, messages, active)
                                     
                    
        messages.append("PASS: Structural validation.")

        return (True, messages, active)            
                 
       

    # CROSS-TREE VALIDATION

    def validate_cross_tree(self, active):

        messages = []

        for (source, targets) in self.fm.cross_tree["requires"
                                                    ].items():

            if source in active:

                for target in targets:

                    if target not in active:

                        messages.append(
                            f"FAIL: {source} requires "
                            f"{target}."
                            )

                        return (False, messages)

        
        for (source, targets) in self.fm.cross_tree["excludes"
                                                    ].items():

            if source in active:

                for target in targets:

                    if target in active:

                        messages.append(
                            f"FAIL: {source} excludes "
                            f"{target}."
                            )

                        return (False, messages)
        
        messages.append("PASS: Cross-tree validation.")


        return (True, messages)



    # BUILD GRAPH USING ONLY ACTIVE FEATURES

    def build_graph(self, active):

        active = set(active)

        graph = {feature: [] for feature in active}

        # Structural relations

        for relation_type in ["mandatory", "optional", "xor", "or"]:

            relations = self.fm.structural[relation_type]

            for parent, children in relations.items():

                if parent not in active:
                    continue

                for child in children:

                    if child in active:
                        graph[parent].append((child, relation_type))

        # Requires relations

        for source, targets in self.fm.cross_tree["requires"].items():

            if source not in active:
                continue

            for target in targets:

                if target in active:
                    graph[source].append((target, "requires"))

        return graph

    
    
    # BUILD FULL GRAPH
    #
    # This graph contains ACTIVE + INACTIVE features.
    #
    # We need this graph to discover missing features.
    # 

    def build_full_graph(self):

        graph = defaultdict(list)

        # Structural relations


        for relation_type in ["mandatory", "optional", "xor", "or"]:

            relations = self.fm.structural[relation_type]

            for parent, children in relations.items():

                for child in children:

                    graph[parent].append((child, relation_type))

        # Requires relations

        for source, targets in self.fm.cross_tree["requires"].items():

            for target in targets:

                graph[source].append(
                    (target, "requires")
                )

        return dict(graph)
    

    

    
    
    # FIND INVOCATION PATH

    def find_invocation_path(self, active, target, dependent_features):

        graph = self.build_graph(active)

        queue = deque()

        visited = set()

        parent = {}

        # Start BFS from invocation features

        for invocation_feature in (invocation_features):

            queue.append(invocation_feature)

            visited.add(invocation_feature)

            parent[invocation_feature] = None

        # BFS
    
        while queue:

            current = queue.popleft()

            if current == target:
                break

            for (next_feature, relation) in graph.get(current, []):

                if next_feature not in visited:

                    visited.add(next_feature)

                    parent[next_feature] = (current, relation)

                    queue.append(next_feature)

        
        
        
        complete_graph = self.build_graph(self.fm.features)
        invocation_path_feature_set = self.FindMissingFeature(
            complete_graph, target, dependent_features)
        invocation__feature_needed = invocation_path_feature_set - active
        
        
        # Target unreachable

        if target not in visited:

            return (None, invocation__feature_needed)

        # Reconstruct path

        path = []

        current = target

        while current is not None:

            previous_info = (parent[current])

            if previous_info is None:

                path.append((current,None))

                break

            previous, relation = (previous_info)

            path.append((current, relation))

            current = previous

        path.reverse()

        return (path, invocation__feature_needed)



    def FindMissingFeature(self, complete_graph, target, 
                           dependent_features):
        FeatureListInInvocationPath = set()
        FeatureListInInvocationPath.add(target)
        FeatureListInInvocationPath.update(dependent_features)
        
        target_set = set(FeatureListInInvocationPath)
        
        #print(target)
        #print(complete_graph)
        #print(invocation_features)
        
        for item in target_set:
        
            current = item

            while current not in invocation_features:

                parent_found = False

                for node_tuple in complete_graph:

                    for child, _ in complete_graph[node_tuple]:

                        if child == current:

                            FeatureListInInvocationPath.add(node_tuple)
                            current = node_tuple
                            parent_found = True
                            break

                    if parent_found:
                        break

                # No parent found → stop
                if not parent_found:
                    break

        return FeatureListInInvocationPath
                    
                
                
        
        
    
    # FORMAT PATH

    def format_path(self, path):

        if not path:

            return "No path"

        result = path[0][0]

        for i in range(1, len(path)):

            feature = path[i][0]

            relation = path[i][1]

            result += (f" --{relation}--> "f"{feature}")

        return result



    # ============================================================
    # FIND ALL REACHABLE FEATURES
    # Find all reachable features in the active configuration
    #   from the invocation features
    # ============================================================

    def get_reachable_features(self,
                               active,
                               invocation_features
                               ):

        active = set(active)
        invocation_features = set(invocation_features)

        graph = self.build_graph(active)

        reachable = set()

        queue = deque()

        # Start from every active invocation feature
        for invocation_feature in invocation_features:

            if invocation_feature in active:

                reachable.add(invocation_feature)
                queue.append(invocation_feature)

        # BFS
        while queue:

            current = queue.popleft()

            for neighbour, relation_type in graph.get(
                current, []):

                if neighbour not in reachable:

                    reachable.add(neighbour)
                    queue.append(neighbour)

        return reachable


    # ============================================================
    # 4. FIND ALL PATHS FROM INVOCATION FEATURES TO TARGET
    #
    # Uses FULL graph.
    #
    # This is important because inactive features may be
    # intermediate nodes in the path.
    # ============================================================

    def find_paths_from_invocation(
        self,
        invocation_features,
        target
    ):

        graph = self.build_full_graph()

        paths = []

        def dfs(
            current,
            path,
            visited
        ):

            if current == target:

                paths.append(path.copy())
                return

            for neighbour, relation_type in graph.get(
                current,
                []
            ):

                if neighbour in visited:
                    continue

                visited.add(neighbour)

                path.append(neighbour)

                dfs(
                    neighbour,
                    path,
                    visited
                )

                path.pop()
                visited.remove(neighbour)

        for invocation_feature in invocation_features:

            dfs(
                invocation_feature,
                [invocation_feature],
                {invocation_feature}
            )

        return paths


    # ============================================================
    # 5. FIND MISSING FEATURES
    #
    # For every unreachable feature:
    #
    #   find candidate invocation paths
    #   calculate inactive features on each path
    # ============================================================

    def find_missing_features(
        self,
        active,
        invocation_features,
        unreachable
    ):

        active = set(active)

        missing_information = {}

        for feature in unreachable:

            paths = self.find_paths_from_invocation(
                invocation_features,
                feature
            )

            candidate_paths = []

            for path in paths:

                path_features = set(path)

                missing = path_features - active

                candidate_paths.append({
                    "path": path,
                    "missing": missing
                })

            missing_information[feature] = candidate_paths

        return missing_information


    # ============================================================
    # 6. ANALYSE ADDITION
    #
    # After adding a feature:
    #
    #   1. Check ALL active features.
    #   2. Find reachable features.
    #   3. Find unreachable features.
    #   4. For unreachable features find missing features.
    # ============================================================

    def analyse_addition(
        self,
        active,
        invocation_features
    ):

        active = set(active)

        # --------------------------------------------------------
        # Step 1: Find reachable active features
        # --------------------------------------------------------

        reachable = self.get_reachable_features(
            active,
            invocation_features
        )

        # --------------------------------------------------------
        # Step 2: Find active features that are unreachable
        # --------------------------------------------------------

        unreachable = active - reachable

        # --------------------------------------------------------
        # Step 3: Find missing features for unreachable features
        # --------------------------------------------------------

        missing_features = self.find_missing_features(
            active,
            invocation_features,
            unreachable
        )

        return {
            "reachable": reachable,
            "unreachable": unreachable,
            "missing_features": missing_features
        }


    # ============================================================
    # 7. ANALYSE REMOVAL
    #
    # After removing a feature:
    #
    #   1. Check ALL remaining active features.
    #   2. Find reachable features.
    #   3. Anything active but unreachable becomes a
    #      dependent feature that should also be removed.
    # ============================================================

    def analyse_removal(self,
                        active,
                        invocation_features):

        active = set(active)

 
        # Find reachable features
        # The feature that are reachable from the invocation feature
        # The feature that has at least one invocation path
 

        reachable = self.get_reachable_features(
            active,
            invocation_features
            )

       
        # Remaining active features that cannot be reached
    

        dependent_to_remove = active - reachable

        return dependent_to_remove


    # ============================================================
    # 8. PRINT ADDITION RESULT
    # ============================================================

    def print_addition_result(
        self,
        result
    ):

        print("\n========== ADDITION ANALYSIS ==========")

        print("\nReachable features:")

        for feature in sorted(
            result["reachable"]
        ):

            print("  +", feature)

        print("\nUnreachable features:")

        for feature in sorted(
            result["unreachable"]
        ):

            print("  -", feature)

        print("\nMissing features:")

        for feature, paths in result[
            "missing_features"
        ].items():

            print(
                f"\nFeature: {feature}"
            )

            if not paths:

                print(
                    "  No path exists from "
                    "any invocation feature."
                )

                continue

            for item in paths:

                path = item["path"]
                missing = item["missing"]

                print(
                    "  Path:",
                    " -> ".join(path)
                )

                if missing:

                    print(
                        "  Missing:",
                        ", ".join(
                            sorted(missing)
                        )
                    )

                else:

                    print(
                        "  Path is active."
                    )


    # ============================================================
    # 9. PRINT REMOVAL RESULT
    # ============================================================

    def print_removal_result(
        self,
        result
    ):

        print("\n========== REMOVAL ANALYSIS ==========")

        print(
            "\nRequested feature to remove:",
            result["removed_feature"]
        )

        print("\nRemaining active features:")

        for feature in sorted(
            result["remaining_active"]
        ):

            print("  ", feature)

        print("\nReachable features:")

        for feature in sorted(
            result["reachable"]
        ):

            print("  +", feature)

        print("\nDependent features to remove:")

        for feature in sorted(
            result["dependent_to_remove"]
        ):

            print("  -", feature)