#Feature Model Configuration


feature_model = {

    "features": {
        "TeaStore",
        "WebUI",
        "Authorization",
        "Local Auth",
        "SSO Auth",
        "Google",
        "Facebook",
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

