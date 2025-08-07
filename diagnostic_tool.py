#!/usr/bin/env python3

"""
🔧 ShadowBeta Diagnostic Tool
This script helps diagnose common issues with the ShadowBeta launcher
"""

import sys
import os
import subprocess
import platform

def check_python():
    """Check Python installation"""
    print("🐍 Python Diagnostic:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Platform: {platform.system()} {platform.release()}")
    
def check_tkinter():
    """Check if tkinter is available"""
    print("\n🖥️ GUI Library (tkinter) Check:")
    try:
        import tkinter as tk
        print("   ✅ tkinter is available")
        
        # Test creating a simple window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("   ✅ tkinter GUI test passed")
        return True
    except ImportError as e:
        print(f"   ❌ tkinter not available: {e}")
        print("   💡 Solution:")
        if platform.system() == "Linux":
            print("      sudo apt-get install python3-tk")
            print("      # or")
            print("      sudo yum install tkinter")
        elif platform.system() == "Darwin":  # macOS
            print("      Install Python from python.org (includes tkinter)")
            print("      # or")
            print("      brew install python-tk")
        else:  # Windows
            print("      Reinstall Python from python.org with 'tcl/tk' option checked")
        return False
    except Exception as e:
        print(f"   ⚠️ tkinter error: {e}")
        return False

def check_dependencies():
    """Check required Python modules"""
    print("\n📦 Dependencies Check:")
    
    required_modules = [
        'subprocess',
        'threading', 
        'webbrowser',
        'time',
        'os'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} - missing")

def check_directories():
    """Check if we're in the right directory"""
    print("\n📁 Directory Structure Check:")
    current_dir = os.getcwd()
    print(f"   Current directory: {current_dir}")
    
    required_dirs = ['backend', 'frontend']
    all_good = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/ directory found")
        else:
            print(f"   ❌ {dir_name}/ directory missing")
            all_good = False
    
    if not all_good:
        print("   💡 Solution: Run this diagnostic from the ShadowBeta main directory")
    
    return all_good

def check_launcher_file():
    """Check if launcher file exists and is readable"""
    print("\n🚀 Launcher File Check:")
    launcher_file = "shadowbeta_launcher.py"
    
    if os.path.exists(launcher_file):
        print(f"   ✅ {launcher_file} exists")
        
        # Check if file is readable
        try:
            with open(launcher_file, 'r') as f:
                content = f.read(100)  # Read first 100 chars
            print("   ✅ File is readable")
            
            # Check if executable
            if os.access(launcher_file, os.X_OK):
                print("   ✅ File is executable")
            else:
                print("   ⚠️ File is not executable")
                print("   💡 Solution: chmod +x shadowbeta_launcher.py")
            
        except Exception as e:
            print(f"   ❌ File read error: {e}")
            return False
    else:
        print(f"   ❌ {launcher_file} not found")
        return False
    
    return True

def check_alternative_launchers():
    """Check alternative startup methods"""
    print("\n🔄 Alternative Launchers Check:")
    
    launchers = {
        "Linux/Ubuntu": "start_shadowbeta.sh",
        "macOS": "start_shadowbeta_macos.sh", 
        "Windows": "start_shadowbeta.bat"
    }
    
    for name, filename in launchers.items():
        if os.path.exists(filename):
            print(f"   ✅ {name}: {filename}")
        else:
            print(f"   ❌ {name}: {filename} missing")

def run_simple_test():
    """Run a simple Python GUI test"""
    print("\n🧪 Simple GUI Test:")
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        print("   Creating test window...")
        root = tk.Tk()
        root.title("ShadowBeta Test")
        root.geometry("300x200")
        
        label = tk.Label(root, text="✅ If you see this window,\nGUI is working!")
        label.pack(pady=50)
        
        button = tk.Button(root, text="Close Test", command=root.quit)
        button.pack()
        
        print("   ✅ Test window created successfully!")
        print("   💡 Close the test window to continue...")
        
        root.mainloop()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"   ❌ GUI test failed: {e}")
        return False

def provide_solutions():
    """Provide common solutions"""
    print("\n💡 Common Solutions:")
    print("=" * 40)
    
    print("\n1. 🐍 Python Issues:")
    print("   • Make sure Python 3.7+ is installed")
    print("   • Try: python3 shadowbeta_launcher.py")
    print("   • Or: python shadowbeta_launcher.py")
    
    print("\n2. 🖥️ GUI Issues (tkinter):")
    system = platform.system()
    if system == "Linux":
        print("   • Ubuntu/Debian: sudo apt-get install python3-tk")
        print("   • CentOS/RHEL: sudo yum install tkinter")
        print("   • Fedora: sudo dnf install python3-tkinter")
    elif system == "Darwin":
        print("   • Install Python from python.org")
        print("   • Or: brew install python-tk")
    else:
        print("   • Reinstall Python from python.org")
        print("   • Make sure 'tcl/tk and IDLE' is checked")
    
    print("\n3. 🔧 Alternative Methods:")
    print("   • Try the script launchers instead:")
    if system == "Linux":
        print("     ./start_shadowbeta.sh")
    elif system == "Darwin":
        print("     ./start_shadowbeta_macos.sh")
    else:
        print("     start_shadowbeta.bat")
    
    print("\n4. 📁 Directory Issues:")
    print("   • Make sure you're in the ShadowBeta main directory")
    print("   • Directory should contain: backend/, frontend/, *.py files")
    
    print("\n5. 🚀 Manual Start:")
    print("   • cd backend && python server.py")
    print("   • cd frontend && yarn start")

def main():
    print("🔧 ShadowBeta Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    check_python()
    tkinter_ok = check_tkinter()
    check_dependencies()
    dirs_ok = check_directories()
    launcher_ok = check_launcher_file()
    check_alternative_launchers()
    
    # Overall assessment
    print("\n📊 Overall Assessment:")
    print("=" * 30)
    
    if tkinter_ok and dirs_ok and launcher_ok:
        print("✅ Most components look good!")
        
        # Run GUI test if everything looks good
        if input("\n🧪 Run GUI test? (y/n): ").lower().startswith('y'):
            if run_simple_test():
                print("✅ GUI test passed! The launcher should work.")
            else:
                print("❌ GUI test failed. Check solutions below.")
                provide_solutions()
        else:
            provide_solutions()
    else:
        print("❌ Issues detected. See solutions below.")
        provide_solutions()
    
    print("\n🆘 If you're still having issues:")
    print("   1. Copy the exact error message")
    print("   2. Run this diagnostic and share the output")
    print("   3. Try the alternative startup methods")

if __name__ == "__main__":
    main()