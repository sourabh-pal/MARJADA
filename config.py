class Configuration:

    def __init__(
        self,
        feature_model,
        active_features
    ):

        self.feature_model = feature_model

        self.active = set(active_features)

        self.inactive = (self.feature_model.features - self.active)

    # --------------------------------------------------------
    # Update configuration
    # --------------------------------------------------------

    def update(self, active_features):

        self.active = set(active_features)

        self.inactive = (self.feature_model.features - self.active)

