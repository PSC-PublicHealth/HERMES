import _winreg, sys, platform

def main():
    """
    Sets Compatibility Properties for the Python interpreter you run this script with as to
    Disable display scaling on high DPI settings
    
    This is necessary to overcome a bug in Chromium Embedded Framework on Windows
    """
    assert platform.system() == "Windows", "This script is only relevant for MS Windows"
    
    REG_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
    registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_WRITE)
    _winreg.SetValueEx(registry_key, sys.executable, 0, _winreg.REG_SZ, "HIGHDPIAWARE")
    _winreg.CloseKey(registry_key)

if __name__=='__main__':
    main()