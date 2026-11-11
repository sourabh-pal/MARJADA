
#Feature Model Configuration

root_feature = "AdaptableTeaStore"

invocation_features = {"WebUI"}

feature_model = {

    "features": {
        "AdaptableTeaStore",
        "WebUI",
        "Authorization",
        "LocalAuth"
    },

    # Structural relationships
    "structural": {
        # Mandatory:
        # If parent is active, child must be active.
        # if child is active, parent must be active.
        "mandatory": {

            "AdaptableTeaStore": [
                "WebUI"
            ],

            "WebUI": [
                "Authorization"
            ]
        },

        # Optional:
        # If parent is active, child may be active or inactive.
        # if child is active, parent must be active.
        "optional": {

            "AdaptableTeaStore": [
                "LocalAuth"
            ]
        },

        # XOR:
        # Exactly one child must be active when parent is active.
        "xor": {
            
    
        },

        # OR:
        # At least one child must be active when parent is active.
        "or": {
            
               }
    },

    # Cross-tree constraints
    "cross_tree": {

        "requires": {

            "WebUI": [
                "LocalAuth"
            ]
        },
        
        "excludes":{
        
        "Authorization": [
                "LocalAuth"
            ]
        
            }
    }
}


barebone_features = {

    "AdaptableTeaStore",

    "WebUI"
}
