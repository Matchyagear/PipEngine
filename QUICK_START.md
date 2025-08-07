# 🚀 ShadowBeta Quick Start Guide

## ✅ **Working Launchers**

### 🎯 **Simple Launcher (RECOMMENDED)**
- **File**: `launch_simple.bat`
- **Status**: ✅ **WORKING**
- **Use**: Double-click to start everything automatically

### 🛠️ **Manual Launcher (For Troubleshooting)**
- **File**: `launch_manual.bat`
- **Status**: ✅ **WORKING**
- **Use**: Choose which services to start individually

## 🚀 **How to Start ShadowBeta**

### **Option 1: Simple Launch (Recommended)**
1. Double-click `launch_simple.bat`
2. Wait for both windows to open
3. Browser will open automatically
4. Keep both backend and frontend windows open

### **Option 2: Manual Launch (For Troubleshooting)**
1. Double-click `launch_manual.bat`
2. Choose option 3 "Start Both Services"
3. Or start services individually (options 1 & 2)

## 🌐 **Access URLs**

Once running:
- **Dashboard**: http://localhost:3000 (or 3001 if 3000 is occupied)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 **Troubleshooting**

### **If the app doesn't load:**

1. **Check if both windows are open:**
   - You should see "ShadowBeta Backend" window
   - You should see "ShadowBeta Frontend" window
   - Both must stay open

2. **Check the backend window:**
   - Should show "✅ MongoDB connected successfully"
   - Should show "INFO: Uvicorn running on http://0.0.0.0:8000"

3. **Check the frontend window:**
   - Should show "Local: http://localhost:3000"
   - Should show "Compiled successfully"

4. **Wait for data to load:**
   - The dashboard may show a white screen initially
   - Wait 10-15 seconds for stock data to load
   - Check the browser console for any errors

### **If services won't start:**

1. **Use the Manual Launcher:**
   - Run `launch_manual.bat`
   - Start backend first (option 1)
   - Check for error messages
   - Then start frontend (option 2)

2. **Check prerequisites:**
   - Python 3.8+ installed
   - Node.js 16+ installed
   - Yarn installed (`npm install -g yarn`)

3. **Port conflicts:**
   - The launchers automatically kill existing processes
   - If you see "port occupied" errors, wait a moment and try again

### **If you see a white screen:**

1. **Wait longer** - Data loading can take 10-15 seconds
2. **Check browser console** (F12) for errors
3. **Verify backend is running** at http://localhost:8000
4. **Try refreshing the page**

## 📊 **What You Should See**

When working correctly:
- **Backend window**: Shows server startup and MongoDB connection
- **Frontend window**: Shows React compilation and local URL
- **Browser**: Shows ShadowBeta dashboard with stock data
- **Stock data**: Real-time prices, charts, and analysis

## 🎯 **Quick Commands**

```bash
# Simple launch
launch_simple.bat

# Manual launch
launch_manual.bat

# Test backend
curl http://localhost:8000/

# Test frontend
curl http://localhost:3000/
```

## 💡 **Tips**

- **Keep both windows open** - closing them stops the services
- **First launch takes longer** - subsequent launches are faster
- **Check console windows** for any error messages
- **API keys are pre-configured** - no setup needed
- **Data loads automatically** - just wait for it to appear

---

**🎉 Happy Trading! 🚀📈**
