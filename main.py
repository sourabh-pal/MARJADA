# RUN GUI

from mainGui import MARJADAGUI
import tkinter as tk
from data import feature_model
from model import FeatureModel
from config import Configuration
from adaptation import AdaptationEngine
from barebone import initial_active


if __name__ == "__main__":

    root = tk.Tk()
    
    fm = FeatureModel(feature_model)
    configuration = Configuration(fm,initial_active)
    engine = AdaptationEngine(fm,configuration)


    app = MARJADAGUI(
        root,
        fm,
        configuration,
        engine
    )

    root.mainloop()