# if using drivers over RPyC, sometimes this obtain() method is useful
try:
    from rpyc.utils.classic import obtain
except ModuleNotFoundError:
    def obtain(x):
        return x
