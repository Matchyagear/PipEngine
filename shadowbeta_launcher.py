#!/usr/bin/env python3

"""
🚀 ShadowBeta Financial Dashboard - GUI Launcher
A simple GUI launcher for the ShadowBeta Financial Dashboard
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import webbrowser
import time

class ShadowBetaLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 ShadowBeta Financial Dashboard Launcher")
        self.root.geometry("600x500")
        self.root.configure(bg='#1e293b')
        
        # Variables
        self.process = None
        self.is_running = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#1e293b')
        title_frame.pack(pady=20)
        
        title_label = tk.Label(
            title_frame, 
            text="🚀 ShadowBeta Financial Dashboard",
            font=("Arial", 18, "bold"),
            fg='#60a5fa',
            bg='#1e293b'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Professional Trading Analysis Platform",
            font=("Arial", 10),
            fg='#94a3b8',
            bg='#1e293b'
        )
        subtitle_label.pack()
        
        # Status Frame
        status_frame = tk.Frame(self.root, bg='#1e293b')
        status_frame.pack(pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="📊 Ready to launch",
            font=("Arial", 12),
            fg='#22c55e',
            bg='#1e293b'
        )
        self.status_label.pack()
        
        # Buttons Frame
        button_frame = tk.Frame(self.root, bg='#1e293b')
        button_frame.pack(pady=20)
        
        # Start Button
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Start ShadowBeta",
            font=("Arial", 14, "bold"),
            bg='#3b82f6',
            fg='white',
            command=self.start_application,
            width=20,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.start_button.pack(pady=5)
        
        # Stop Button
        self.stop_button = tk.Button(
            button_frame,
            text="🛑 Stop Application",
            font=("Arial", 12),
            bg='#ef4444',
            fg='white',
            command=self.stop_application,
            width=20,
            height=1,
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.stop_button.pack(pady=5)
        
        # Open Browser Button
        self.browser_button = tk.Button(
            button_frame,
            text="🌐 Open Dashboard",
            font=("Arial", 12),
            bg='#10b981',
            fg='white',
            command=self.open_dashboard,
            width=20,
            height=1,
            relief='flat',
            cursor='hand2'
        )
        self.browser_button.pack(pady=5)
        
        # Log Frame
        log_frame = tk.Frame(self.root, bg='#1e293b')
        log_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        log_label = tk.Label(
            log_frame,
            text="📋 Application Log:",
            font=("Arial", 10, "bold"),
            fg='#94a3b8',
            bg='#1e293b'
        )
        log_label.pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            bg='#0f172a',
            fg='#e2e8f0',
            font=("Consolas", 9),
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Info Frame
        info_frame = tk.Frame(self.root, bg='#1e293b')
        info_frame.pack(pady=10)
        
        info_label = tk.Label(
            info_frame,
            text="💡 Tip: Make sure you have added your API keys to backend/.env file",
            font=("Arial", 9),
            fg='#fbbf24',
            bg='#1e293b'
        )
        info_label.pack()
        
    def log_message(self, message):
        """Add message to log"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()
        
    def start_application(self):
        """Start the ShadowBeta application"""
        if self.is_running:
            messagebox.showwarning("Already Running", "ShadowBeta is already running!")
            return
            
        self.log_message("🚀 Starting ShadowBeta Financial Dashboard...")
        self.status_label.config(text="⏳ Starting services...", fg='#fbbf24')
        
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Start in a separate thread
        thread = threading.Thread(target=self._start_services)
        thread.daemon = True
        thread.start()
        
    def _start_services(self):
        """Start services in background thread"""
        try:
            # Determine which script to run
            script_path = None
            if os.name == 'nt':  # Windows
                script_path = os.path.join(os.getcwd(), 'start_shadowbeta.bat')
            else:  # Linux/macOS
                if sys.platform == 'darwin':  # macOS
                    script_path = os.path.join(os.getcwd(), 'start_shadowbeta_macos.sh')
                else:  # Linux
                    script_path = os.path.join(os.getcwd(), 'start_shadowbeta.sh')
            
            if not os.path.exists(script_path):
                self.log_message(f"❌ Startup script not found: {script_path}")
                return
                
            self.log_message(f"📂 Using startup script: {script_path}")
            
            # For supervisor-based systems, use supervisorctl
            if os.path.exists('/usr/bin/supervisorctl'):
                self.log_message("🔄 Starting services with supervisor...")
                subprocess.run(['sudo', 'supervisorctl', 'restart', 'all'], check=True)
                self.log_message("✅ Services started successfully!")
            else:
                # Run the appropriate startup script
                if os.name == 'nt':  # Windows
                    self.process = subprocess.Popen([script_path], shell=True)
                else:  # Linux/macOS  
                    self.process = subprocess.Popen(['bash', script_path])
                    
                self.log_message("✅ Startup script executed!")
            
            self.is_running = True
            self.status_label.config(text="🟢 ShadowBeta is running!", fg='#22c55e')
            
            # Wait a bit then try to open browser
            time.sleep(10)
            self.open_dashboard()
            
        except Exception as e:
            self.log_message(f"❌ Error starting application: {str(e)}")
            self.status_label.config(text="❌ Failed to start", fg='#ef4444')
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
    def stop_application(self):
        """Stop the ShadowBeta application"""
        self.log_message("🛑 Stopping ShadowBeta...")
        self.status_label.config(text="⏳ Stopping services...", fg='#fbbf24')
        
        try:
            # For supervisor-based systems
            if os.path.exists('/usr/bin/supervisorctl'):
                subprocess.run(['sudo', 'supervisorctl', 'stop', 'all'], check=True)
                self.log_message("✅ Services stopped successfully!")
            elif self.process:
                self.process.terminate()
                self.log_message("✅ Application process terminated!")
                
            self.is_running = False
            self.status_label.config(text="🔴 Stopped", fg='#ef4444')
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
        except Exception as e:
            self.log_message(f"❌ Error stopping application: {str(e)}")
            
    def open_dashboard(self):
        """Open the dashboard in browser"""
        try:
            # Try to detect the correct URL
            frontend_url = "http://localhost:3000"
            
            # Check if we have environment configuration
            env_file = os.path.join(os.getcwd(), 'frontend', '.env')
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            if 'REACT_APP_BACKEND_URL' in line and '=' in line:
                                backend_url = line.split('=')[1].strip().strip('"')
                                frontend_url = backend_url.replace('/api', '')
                                break
                except:
                    pass
            
            self.log_message(f"🌐 Opening dashboard: {frontend_url}")
            webbrowser.open(frontend_url, new=2)
            
        except Exception as e:
            self.log_message(f"❌ Error opening browser: {str(e)}")
            messagebox.showerror("Browser Error", f"Could not open browser: {str(e)}")

def main():
    # Check if we're in the right directory
    if not os.path.exists('backend') or not os.path.exists('frontend'):
        messagebox.showerror(
            "Directory Error",
            "Please run this launcher from the ShadowBeta application directory.\n"
            "The directory should contain 'backend' and 'frontend' folders."
        )
        return
        
    root = tk.Tk()
    app = ShadowBetaLauncher(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        if app.is_running:
            app.stop_application()

if __name__ == "__main__":
    main()