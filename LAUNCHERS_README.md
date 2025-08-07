# 🚀 ShadowBeta Launchers

This directory contains multiple launcher scripts to start ShadowBeta Financial Dashboard. Choose the one that best fits your needs:

## 📋 Available Launchers

### 🎯 **Quick Start (Recommended for Daily Use)**
- **File**: `start_shadowbeta.bat`
- **Use**: When everything is already set up and you just want to start the app
- **Features**:
  - Kills existing processes
  - Starts backend and frontend
  - Opens browser automatically
  - Minimal setup checks

### 🔧 **Ultimate Launcher (Recommended for First Time)**
- **File**: `launch_shadowbeta_ultimate.bat`
- **Use**: First-time setup or when you need comprehensive setup
- **Features**:
  - Full dependency checking
  - Creates missing .env files
  - Installs Python virtual environment
  - Installs frontend dependencies
  - Comprehensive error handling
  - Port conflict resolution

### ⚡ **PowerShell Ultimate Launcher**
- **File**: `launch_shadowbeta_ultimate.ps1`
- **Use**: Same as Ultimate Launcher but with better error handling
- **Features**:
  - Colored output
  - Better error messages
  - PowerShell-specific optimizations
  - Background job management

### 🛠️ **Legacy Launchers**
- `launch_shadowbeta.bat` - Original comprehensive launcher
- `launch_shadowbeta.ps1` - Original PowerShell launcher
- `start_shadowbeta_simple.bat` - Simple launcher
- `start_without_craco.bat` - Alternative frontend launcher
- `start_shadowbeta_fixed.bat` - Fixed version of simple launcher

## 🚀 How to Use

### **First Time Setup:**
1. Double-click `launch_shadowbeta_ultimate.bat` (or `.ps1`)
2. Wait for all dependencies to install
3. The launcher will open your browser automatically

### **Daily Use:**
1. Double-click `start_shadowbeta.bat`
2. Wait for services to start
3. Browser will open automatically

## 🌐 Access URLs

Once running, you can access:
- **Dashboard**: http://localhost:3000 (or 3001 if 3000 is occupied)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Troubleshooting

### **Port Conflicts**
- The launchers automatically kill existing processes on ports 8000 and 3000
- If you see "port occupied" messages, the launcher will handle it

### **White Screen**
- Wait 10-15 seconds for data to load
- Check that both backend and frontend windows are running
- Verify the backend is responding at http://localhost:8000

### **Missing Dependencies**
- Use the Ultimate Launcher to install all dependencies
- Make sure Python 3.8+ and Node.js 16+ are installed

### **Environment Files**
- The Ultimate Launcher creates missing .env files automatically
- If you need to customize API keys, edit the .env files manually

## 📁 File Structure

```
PipEngine-main/
├── launch_shadowbeta_ultimate.bat    # Comprehensive setup launcher
├── launch_shadowbeta_ultimate.ps1    # PowerShell version
├── start_shadowbeta.bat              # Quick start launcher
├── backend/                          # Backend server
├── frontend/                         # Frontend React app
└── LAUNCHERS_README.md               # This file
```

## 🎯 Quick Commands

If you prefer command line:

```bash
# Quick start
start_shadowbeta.bat

# Full setup
launch_shadowbeta_ultimate.bat

# PowerShell (if available)
powershell -ExecutionPolicy Bypass -File launch_shadowbeta_ultimate.ps1
```

## 💡 Tips

- **Keep both backend and frontend windows open** - closing them stops the services
- **First launch takes longer** - subsequent launches are faster
- **Check the console windows** for any error messages
- **API keys are pre-configured** - you can customize them in the .env files

---

**Happy Trading! 🚀📈**
