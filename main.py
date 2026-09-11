# RUN GUI

from mainGui import MARJADAGUI
import tkinter as tk
from data import feature_model, root_feature
from model import FeatureModel
from config import Configuration
from adaptation import AdaptationEngine
from barebone import initial_active, VerifyBarebone


if __name__ == "__main__":

    root = tk.Tk()
    
    # get the feature model with structural, and cross-tree constraints relations.
    fm = FeatureModel(feature_model)
    callVerifyBarebone = VerifyBarebone(root_feature, fm)
    isInitialState = callVerifyBarebone.is_initial_active_configuration(root_feature, fm)
    
    configuration = Configuration(fm,initial_active)
    engine = AdaptationEngine(fm,configuration)


    app = MARJADAGUI(
        root,
        fm,
        configuration,
        engine
    )

    root.mainloop()