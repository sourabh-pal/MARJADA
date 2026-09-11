
#Feature Model Configuration

root_feature = "AdaptableTeaStore"

feature_model = {

    "features": {
        "AdaptableTeaStore",
        "WebUI",
        "Authorization",
        "LocalAuth",
        "SSOAuth",
        "Google",
        "Facebook",
        "Persistence",
        "LocalCache",
        "LocalStaticDB",
        "ImageService",
        "ImageProvider",
        "LocalStaticImg",
        "PageCompilation",
        "PageInformation",
        "BasicPageInfo",
        "AuthoPageInfo",
        "PageImages",
        "CompilationWithRecom",
        "Recommender",
        "LowPower",
        "FullPower"
    },

    # Structural relationships
    "structural": {
        # Mandatory:
        # If parent is active, child must be active.
        # if child is active, parent must be active.
        "mandatory": {

            "AdaptableTeaStore": [
                "WebUI",
                "Persistence",
                "ImageService",
                "PageCompilation"
            ],

            "PageCompilation": [
                "PageInformation",
                "PageImages"
            ]
        },

        # Optional:
        # If parent is active, child may be active or inactive.
        # if child is active, parent must be active.
        "optional": {

            "AdaptableTeaStore": [
                "Authorization", "Recommender"
            ],

            "PageCompilation": [
                "CompilationWithRecom"
            ]
        },

        # XOR:
        # Exactly one child must be active when parent is active.
        "xor": {
            
            "Authorization":[
                "LocalAuth",
                "SSOAuth"
                ],
            "Persistence":[
                "LocalCache",
                "LocalStaticDB"
            ],
            "ImageService": [
                "ImageProvider",
                "LocalStaticImg"
            ],
            "Recommender": [
                "LowPower",
                "FullPower"
            ]
        },

        # OR:
        # At least one child must be active when parent is active.
        "or": {
            
            "SSOAuth":[
                "Google",
                "Facebook"
                ],
            "PageInformation":[
                "BasicPageInfo",
                "AuthoPageInfo"
                ]
        }
    },

    # Cross-tree constraints
    "cross_tree": {

        "requires": {

            "WebUI": [
                "PageCompilation"
            ],
            "PageCompilation": [
                "Persistence",
                "ImageService"
            ],
            "PageInformation": [
                "Persistence"
            ],
            "BasicPageInfo":[
                "Persistence"
                ],
            "AuthoPageInfo":[
                "Authorization"
                ],
            "PageImages":[
                "ImageService"
                ],
            "CompilationWithRecom": [
                "Persistence",
                "ImageService",
                "Recommender"
            ],
            "Recommender": [
                "Persistence"
            ],
            "LowPower": [
                "Persistence"
            ],
            "FullPower": [
                "PageInformation"
            ]
        }
    }
}

