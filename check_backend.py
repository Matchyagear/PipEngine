import os
import sys
import subprocess
import time

def check_python():
    print("\n=== Python Check ===")
    try:
        python_version = subprocess.check_output(["python", "--version"], stderr=subprocess.STDOUT, text=True)
        print(f"Python version: {python_version.strip()}")
        return True
    except Exception as e:
        print(f"Error getting Python version: {e}")
        return False

def check_requirements():
    print("\n=== Requirements Check ===")
    try:
        import fastapi
        import uvicorn
        print(f"FastAPI version: {fastapi.__version__}")
        print(f"Uvicorn version: {uvicorn.__version__}")
        return True
    except ImportError as e:
        print(f"Missing requirements: {e}")
        return False

def start_server():
    print("\n=== Starting Server ===")
    try:
        # Change to backend directory
        os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Start the server in the background
        server_process = subprocess.Popen(
            ["python", "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it some time to start
        print("Server starting... (waiting 5 seconds)")
        time.sleep(5)
        
        # Check if the process is still running
        if server_process.poll() is not None:
            print("Server failed to start!")
            stdout, stderr = server_process.communicate()
            print("\n=== Server Output ===")
            print(stdout)
            print("\n=== Server Error ===")
            print(stderr)
            return False
        
        print("Server started successfully!")
        print("Press Ctrl+C to stop the server")
        
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\nStopping server...")
            server_process.terminate()
            
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def main():
    print("ShadowBeta Backend Diagnostic Tool")
    print("=" * 40)
    
    if not check_python():
        print("\n❌ Python check failed")
        return
    
    if not check_requirements():
        print("\n❌ Requirements check failed")
        print("Please install requirements with: pip install -r backend/requirements.txt")
        return
    
    print("\n✅ All checks passed!")
    print("\nAttempting to start the server...")
    start_server()

if __name__ == "__main__":
    main()
