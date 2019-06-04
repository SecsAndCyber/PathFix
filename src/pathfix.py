import sys, os, os.path, argparse, ctypes
from ctypes.wintypes import HWND, UINT, WPARAM, LPARAM, LPVOID, c_wchar_p
import ConfigParser
import logging
import time
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
LRESULT = LPARAM

config = ConfigParser.RawConfigParser(allow_no_value=True)

def _NotifyWindows():
    SendMessageTimeout = ctypes.windll.user32.SendMessageTimeoutW
    SendMessageTimeout.argtypes = HWND, UINT, WPARAM, c_wchar_p, UINT, UINT, UINT
    SendMessageTimeout.restype = LRESULT
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_NORMAL = 0x000
    SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_NORMAL, 10, 0)

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
            _NotifyWindows()
        except WindowsError as werr:
            print 'Unabled to succeed: \n\t%s' % werr

def ListVariable(Env):
    if Env in os.environ:
        print Env
        for env in os.environ[Env].split(";"):
            print '  ',env
    else:
        msg = '%s is not a recognized environment variable %s' % (Env, os.environ.keys)
        print msg
        logging.warn(msg)
    
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
        Env_set = set()
        index = 0
        for env in os.environ[Envs].split(";"):
            if env.lower() in Env_set: continue
            Env_set.add(env.lower())
            if env:
                config.set(Envs, str(index), env)
                index += 1
        
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
    
def InstallConfig(ConfigPath, CurrentUser=True):
    Reg = __import__("_winreg")
    
    if CurrentUser:
        path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        reg = Reg.ConnectRegistry(None, Reg.HKEY_CURRENT_USER)
        KeyName = 'HKEY_CURRENT_USER'
    else:
        raise ArgumentError("Only user installation is supported at this time")
        
    Startup = ""
    with Reg.OpenKey(reg, path, 0, Reg.KEY_ALL_ACCESS) as key:
        index = 0
        try:
            while True:
                v_name, v_data, v_data_type = Reg.EnumValue(key, index)
                if v_name.lower() == "startup":
                    Startup = v_data
                index += 1        
        except WindowsError:
            pass
            
    if Startup:
        logging.info("Saving setup batch file to %s", Startup)
        PythonFilePath = os.path.abspath(os.path.dirname(sys.argv[0]))
        StartupBat = os.path.join(Startup, "pathfix.bat")
        if not os.path.splitdrive(StartupBat)[0] == os.path.splitdrive(PythonFilePath)[0]:
            cd_args = "/d "
        else:
            cd_args = ""
        # ToDo: detect proper call to python!
        with open(StartupBat, "w") as StartupBatFile:
            StartupBatFile.write("cd {}{}\n".format(cd_args, PythonFilePath))
            StartupBatFile.write("python %s -c -a %s\n" % ( sys.argv[0], ConfigPath ))
        with open(StartupBat, "r") as StartupBatFile:
            logging.info(StartupBatFile.read())
    
    
def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-a",action="store", dest='apply', help='apply the config to environment variables')
    parser.add_argument("-l",action="store", dest='list', default=None, help='display the current contents of variable')
    parser.add_argument("-e",action="store", dest='export', help='writes current environment variables to config')
    parser.add_argument("-p",action="store", dest='preview', help='parses and prints the config without modifying the environment')
    parser.add_argument("-c",action="store_true", dest='current', default=False, help='Limit applied changes to current user (Defaults to all users)')
    parser.add_argument("-i",action="store", dest='install', help='apply the config to environment variables on every startup')
    parser.add_argument("-v",action="count", dest='verbose', help='logging verbosity')
    args = parser.parse_args()
    
    if args.verbose > 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose:
        logging.basicConfig(level=logging.WARN)
    else:
        logging.basicConfig(filename=os.path.join(CUR_DIR, 'pathfix.log'), level=logging.INFO)
        
        
    logging.info("Running %s at %s", "{}".format(args), time.ctime())
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
        
    if args.install:
        InstallConfig(args.install, CurrentUser=args.current)
        return
    
    parser.parse_args(['--help'])
    
if __name__ == "__main__":
    main()