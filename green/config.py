try:
    import ConfigParser as cp
except:
    import configparser as cp
import os

def get_config():
    try:
        rval = get_config._cfg
    except AttributeError:
        load_config()
        rval = get_config._cfg

    return rval

def load_config(cmdline=None):
    if hasattr(get_config, "_cfg"):
        return
    
    get_config._cfg = cp.ConfigParser()
    if cmdline is not None:
        get_config._cfg.read(cmdline)
        return
    
    env = os.getenv("GREEN_CONF")
    if env is not None:
        get_config._cfg.read(env)
        return

    home = os.getenv("HOME")
    if home is not None:
        get_config._cfg.read(os.path.join(home, ".green"))
