
initial_active = {

    "AdaptableTeaStore",

    "WebUI",

    "Persistence",
    "LocalCache",

    "ImageService",
    "ImageProvider",

    "PageCompilation",

    "PageInfo",
    "BasicPageInfo",

    "PageImages"
}

class VerifyBarebone:
    def __init__(self, root_feature, fm):
        self.root_feature = root_feature
        self.fm = fm

    def is_initial_active_configuration(self, root_feature, fm):
        print(self.fm.structural["mandatory"].keys())
        print(self.fm.structural["mandatory"].values())
        print(self.fm.structural["xor"].keys())
        print(self.fm.structural["xor"].values())
        print(self.root_feature)
    
        
        return 0