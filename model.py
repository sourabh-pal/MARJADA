# FEATURE MODEL


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
