# RUN GUI

from mainGui import MARJADAGUI
import tkinter as tk
from data import root_feature, feature_model, barebone_features
from model import FeatureModel
from config import Configuration
from adaptation import AdaptationEngine


if __name__ == "__main__":

    root = tk.Tk()
    
    # get the feature model with structural, and cross-tree constraints relations.
    fm = FeatureModel(feature_model)
    
    initial_active = barebone_features
    configuration = Configuration(fm,initial_active)
    
    
    engine = AdaptationEngine(fm,configuration)


    app = MARJADAGUI(
        root,
        fm,
        configuration,
        engine
    )

    root.mainloop()