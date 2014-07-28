import sys, os, argparse
import ConfigParser

config = ConfigParser.RawConfigParser(allow_no_value=True)

def WriteVar(value, Var, CurrentUser=False):
    """ Help? """
    if not Var:
        raise ArgumentError
    Reg = __import__("_winreg")
    if CurrentUser:
        path = r'Environment'
        reg = Reg.ConnectRegistry(None, Reg.HKEY_CURRENT_USER)
        KeyName = 'HKEY_CURRENT_USER'
    else:
        path = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
        reg = Reg.ConnectRegistry(None, Reg.HKEY_LOCAL_MACHINE)
        KeyName = 'HKEY_LOCAL_MACHINE'
        
    with Reg.OpenKey(reg, path, 0, Reg.KEY_ALL_ACCESS) as key:
        try:
            if value:
                print r'Writing "%s" to "%s\%s"' % ( Var, KeyName, path )
                Reg.SetValueEx(key, Var, 0, Reg.REG_EXPAND_SZ, value)
            else:
                print r'Deleting "%s" from "%s\%s"' % ( Var, KeyName, path )
                Reg.DeleteValue(key, Var)
        except WindowsError as werr:
            print 'Unabled to succeed: \n\t%s' % werr

def ListVariable(Env):
    if Env in os.environ:
        print Env
        for env in os.environ[Env].split(";"):
            print '  ',env
    else:
        print '%s is not a recongnized environment variable %s' % (Env, os.environ.keys)
    
def PreviewConfig(ConfigPath):
    config.read(ConfigPath)
    for section in config.sections():
        print section
        for key, env in config.items(section):
            print '  ',env
    
def ExportToConfig(ConfigPath, EnvVars = None, CurrentUser=False):
    """ 
    Exports current variables to the file at ConfigPath
    If file is not found, a new one is created

    Optionally, EnvVars can be used to limit the exported variables
    """
    
    if CurrentUser:
        if not EnvVars:
            EnvVars = []
        Reg = __import__("_winreg")
        path = r'Environment'
        reg = Reg.ConnectRegistry(None, Reg.HKEY_CURRENT_USER)
        KeyName = 'HKEY_CURRENT_USER'
        with Reg.OpenKey(reg, path, 0, Reg.KEY_ALL_ACCESS) as key:
            index = 0
            try:
                while True:
                    v_name, v_data, v_data_type = Reg.EnumValue(key, index)
                    print v_name, index
                    EnvVars.append(v_name)
                    index += 1        
            except WindowsError:
                pass
    
    for Envs in os.environ:
        if EnvVars and not Envs in EnvVars:
            continue
            
        config.add_section(Envs)
        for x, env in enumerate(os.environ[Envs].split(";")):
            if env:
                config.set(Envs, str(x), env)
        
    with open(ConfigPath, "w") as configfile:
        config.write(configfile)
        
def ApplyConfig(ConfigPath, CurrentUser=False):
    config.read(ConfigPath)
    for section in config.sections():
        path_var = ""
        for key, env in config.items(section):
            path_var += "%s;" % env
        path_var = path_var.strip(";")
        WriteVar(path_var, section, CurrentUser)
    
def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-a",action="store", dest='apply', help='apply the config to environment variables')
    parser.add_argument("-l",action="store", dest='list', default=None, help='display the current contents of variable')
    parser.add_argument("-e",action="store", dest='export', help='writes current environment variables to config')
    parser.add_argument("-p",action="store", dest='preview', help='parses and prints the config without modifying the environment')
    parser.add_argument("-c",action="store_true", dest='current', default=False, help='Limit applied changes to current user (Defaults to all users)')
    args = parser.parse_args()
    
    if args.list:
        ListVariable(args.list)
        return
    
    if args.preview:
        PreviewConfig(args.preview)
        return
    
    if args.export:
        ExportToConfig(args.export, CurrentUser=args.current)
        return
    
    if args.apply:
        ApplyConfig(args.apply, CurrentUser=args.current)
        return
    
    parser.parse_args('--help'.split())
    
if __name__ == "__main__":
    main()