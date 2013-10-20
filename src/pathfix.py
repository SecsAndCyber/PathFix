import sys, os, argparse
import ConfigParser

CONFIG="path.config"

config = ConfigParser.RawConfigParser(allow_no_value=True)

def WritePath(value):
    Reg = __import__("_winreg")
    path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    reg = Reg.ConnectRegistry(None, Reg.HKEY_LOCAL_MACHINE)
    key = Reg.OpenKey(reg, path, 0, Reg.KEY_ALL_ACCESS)    
    Reg.SetValueEx(key, 'PATH', 0, Reg.REG_EXPAND_SZ, value)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("CONFIG")
    parser.add_argument("-a","--apply",action="store_true")
    parser.add_argument("-l","--list",action="store_true")
    parser.add_argument("-w","--write",action="store_true")
    parser.add_argument("-p","--preview",action="store_true")
    args = parser.parse_args()

    if args.list:
        for env in os.environ["PATH"].split(";"):
            print env
        return
    
    if args.preview:
        config.read(args.CONFIG)
        for key, env in config.items('PATH'):
            print env
        return
    
    if args.write:
        config.add_section('PATH')

        for x, env in enumerate(os.environ["PATH"].split(";")):
            if env:
                config.set('PATH', str(x), env)
            
        with open(args.CONFIG, "w") as configfile:
            config.write(configfile)
        return
    
    if args.apply:
        config.read(args.CONFIG)
        path_var = ""
        for key, env in config.items('PATH'):
            path_var += "%s;" % env
        WritePath(path_var)
        return
    
    pass
    
if __name__ == "__main__":
    main()