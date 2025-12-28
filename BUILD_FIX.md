# Build Issue - Admin Required

## Problem
Build failing due to permission error: "Cannot create symbolic link : A required privilege is not held by the client"

## Solutions

### Option 1: Run as Administrator (Recommended)
1. Close current PowerShell
2. Right-click PowerShell → **Run as Administrator**
3. Run build command:
```powershell
cd "C:\Users\gh\Desktop\Clinic app\electron"
npm run build-win
```

### Option 2: Enable Developer Mode (One-time)
1. Open **Windows Settings**
2. Go to **Update & Security** → **For Developers**
3. Turn ON **Developer Mode**
4. Restart PowerShell
5. Run build again

### Option 3: Use Development Mode (Quick Test)
Run app without building:
```powershell
cd "C:\Users\gh\Desktop\Clinic app\electron"
npm start
```

This will launch the app immediately without creating installer.

### Option 4: Delete Cache and Retry
```powershell
Remove-Item "$env:LOCALAPPDATA\electron-builder\Cache" -Recurse -Force
cd "C:\Users\gh\Desktop\Clinic app\electron"
npm run build-win
```

---

## Alternative: Simpler Build Script

I've created a batch file that handles this automatically:
