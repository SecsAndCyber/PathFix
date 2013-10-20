import sys, os, argparse
import ConfigParser

CONFIG="path.config"

config = ConfigParser.RawConfigParser(allow_no_value=True)

def WriteVar(value, Var):
    Reg = __import__("_winreg")
    win32gui = __import__("win32gui")
    win32con = __import__("win32con")
    path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    reg = Reg.ConnectRegistry(None, Reg.HKEY_LOCAL_MACHINE)
    key = Reg.OpenKey(reg, path, 0, Reg.KEY_ALL_ACCESS)  
    if Var:
        Reg.SetValueEx(key, Var, 0, Reg.REG_EXPAND_SZ, value)
    else:
        Reg.DeleteValue(key, Var)
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("CONFIG")
    parser.add_argument("-a","--apply",action="store_true")
    parser.add_argument("-l","--list",action="store_true")
    parser.add_argument("-w","--write",action="store_true")
    parser.add_argument("-p","--preview",action="store_true")
    args = parser.parse_args()
    
    config.read(args.CONFIG)

    if args.list:
        for env in os.environ["PATH"].split(";"):
            print env
        return
    
    if args.preview:
        for section in config.sections():
            print section
            for key, env in config.items(section):
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
        for section in config.sections():
            path_var = ""
            for key, env in config.items(section):
                path_var += "%s;" % env
            path_var = path_var.strip(";")
            WriteVar(path_var, section)
        return
    
    pass
    
if __name__ == "__main__":
    main()