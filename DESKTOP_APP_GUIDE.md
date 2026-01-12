# 🖥️ Desktop App Setup Guide

## Overview
This will package your clinic app as a Windows Desktop Application (.exe) that:
- ✅ Auto-starts Django server
- ✅ Auto-detects IP address
- ✅ Shows dashboard with server info
- ✅ Easy to install on all 3 laptops
- ✅ No command line needed!

---

## 📋 Prerequisites

You need **Node.js** installed. Download from: https://nodejs.org/

---

## 🚀 Build Desktop App

### Step 1: Install Node.js Dependencies

Open PowerShell in the `electron` folder:

```powershell
cd "C:\Users\gh\Desktop\Clinic app\electron"
npm install
```

This installs:
- Electron (creates desktop window)
- Electron Builder (packages as .exe)

### Step 2: Build the App

Still in `electron` folder:

```powershell
npm run build-win
```

This creates:
- `dist/Clinic Management Setup 1.0.0.exe` (Installer)
- Takes 5-10 minutes first time

---

## 📦 What You Get

After building, you'll have in `electron/dist/`:

1. **Clinic Management Setup 1.0.0.exe** 
   - Full installer (100-150 MB)
   - Installs app like normal Windows software
   - Auto-creates desktop shortcut
   - **Use this for installation**

2. **win-unpacked/** folder
   - Portable version (no installation needed)
   - Can copy to USB and run directly

---

## 💿 Install on All 3 Laptops

### Option A: Using Installer (Recommended)

1. Copy `Clinic Management Setup 1.0.0.exe` to USB drive
2. Insert USB in each laptop
3. Double-click the installer
4. Follow installation wizard
5. Launch from Start Menu or Desktop shortcut

### Option B: Portable Version

1. Copy entire `win-unpacked` folder to USB
2. On each laptop, copy folder to `C:\Program Files\`
3. Run `Clinic Management.exe` from the folder
4. Create desktop shortcut manually

---

## 🎯 How It Works

### On SERVER Laptop:

1. **Launch the app** (double-click icon)
2. App automatically:
   - Starts Django server
   - Detects local IP address
   - Shows dashboard with connection info
3. **Share the IP** shown in the app with other laptops
4. **Keep app running** all day

### On CLIENT Laptops (Doctor, OPD, Pharmacy):

**Option 1: Use the Desktop App**
1. Launch the app
2. Click on panel buttons (Doctor/OPD/Pharmacy)
3. Opens in your default browser

**Option 2: Just Use Browser**
1. Open any browser
2. Type the server IP (shown on server laptop)
3. Login to your panel

---

## 🔥 Features

### Dashboard Shows:
- 📡 **Server IP** - Auto-detected, ready to copy
- 🌐 **Full URL** - Complete link to share
- 🚀 **Quick Access Buttons** - Click to open panels
- 📖 **Instructions** - How to connect other laptops
- ↻ **Restart Server** - If something goes wrong
- 📝 **Server Log** - See what's happening

### Auto Features:
- ✅ Auto-start Django on app launch
- ✅ Auto-detect local IP address
- ✅ Auto-stop Django on app close
- ✅ No command line needed
- ✅ No manual configuration

---

## 📁 File Structure

```
Clinic app/
├── manage.py
├── db.sqlite3
├── (all your Django files)
└── electron/
    ├── package.json       ← Node.js config
    ├── main.js           ← Electron main process
    ├── preload.js        ← Security bridge
    ├── renderer.js       ← Dashboard logic
    ├── index.html        ← Dashboard UI
    ├── styles.css        ← Dashboard styles
    └── dist/             ← Built app appears here
        └── Clinic Management Setup 1.0.0.exe
```

---

## 🔧 Development vs Production

### Development Mode (Testing):
```powershell
cd electron
npm start
```
- Quick launch for testing
- Uses local Django files directly
- No build needed

### Production Mode (Distribution):
```powershell
cd electron
npm run build-win
```
- Creates installer
- Packages everything together
- Ready to distribute

---

## 🎨 Customize (Optional)

### Change App Name:
Edit `electron/package.json`:
```json
{
  "name": "your-clinic-name",
  "productName": "Your Clinic Management"
}
```

### Change App Icon:
1. Create 256x256 PNG icon
2. Convert to .ico file (use online converter)
3. Save as `electron/icon.ico`
4. Rebuild app

### Change Colors:
Edit `electron/styles.css` - change gradient colors

---

## 🚨 Troubleshooting

### "npm not found"
**Solution:** Install Node.js from https://nodejs.org/

### "Build failed"
**Solution:** 
```powershell
cd electron
npm install
npm run build-win
```

### "App won't start"
**Solutions:**
- Make sure Python virtual environment exists
- Check `env/Scripts/python.exe` is present
- Verify Django runs manually first

### "Can't find server"
**Solutions:**
- Check Windows Firewall allows port 8000
- Check network cables connected
- Restart the app

### "Database locked"
**Solution:**
- Only run ONE server instance
- Close old app before starting new one

---

## 📊 Comparison: Desktop App vs Manual

| Feature | Desktop App | Manual (BAT file) |
|---------|-------------|-------------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Auto IP Detection** | ✅ Yes | ❌ Manual |
| **Dashboard UI** | ✅ Beautiful | ❌ None |
| **Installation** | ✅ Installer | ❌ Manual copy |
| **Desktop Shortcut** | ✅ Auto | ❌ Manual |
| **Professional Look** | ✅ Yes | ❌ Command window |
| **User Friendly** | ✅ Very | ⭐⭐ |

---

## 🎯 Recommended Setup

### For Your Clinic:

1. **Build the Desktop App** (one time)
   ```powershell
   cd electron
   npm install
   npm run build-win
   ```

2. **Install on ALL 3 Laptops**
   - Use the installer from `dist/`
   - Same app on all laptops

3. **Daily Usage:**
   - **Server Laptop:** Launch app, note IP address
   - **Client Laptops:** Launch app, click panel buttons

4. **Network Setup:**
   - Connect all via Ethernet switch
   - Or use existing Wi-Fi (local only)

---

## 🌐 LAN Setup (After App Install)

The app works with both:

### Option A: Wi-Fi Network (Easiest)
- All laptops connect to same Wi-Fi
- No cables needed
- Server laptop must be on network
- App auto-detects IP

### Option B: Ethernet LAN (Faster, No Internet)
- Connect all laptops via Ethernet switch
- Set static IPs (optional)
- No internet required
- More reliable

**Read `LAN_SETUP_GUIDE.md` for network details**

---

## ✅ Quick Start Checklist

- [ ] Node.js installed
- [ ] Run `npm install` in electron folder
- [ ] Run `npm run build-win`
- [ ] Find installer in `dist/` folder
- [ ] Copy installer to USB
- [ ] Install on all 3 laptops
- [ ] Launch app on server laptop
- [ ] Note the IP address shown
- [ ] Launch app on client laptops
- [ ] Click panel buttons to access

---

## 🎉 Done!

You now have a professional desktop application that:
- Looks professional
- Easy to use
- Auto-detects everything
- Works offline
- Ready to distribute

**Next:** Connect laptops via LAN and start using!
