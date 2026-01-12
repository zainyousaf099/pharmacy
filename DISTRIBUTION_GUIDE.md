# Clinic Management System - Distribution Guide

## 📦 Your Installer is Ready!

**Location:** `electron\dist\Clinic Management System Setup 1.0.0.exe`  
**Size:** ~118 MB

---

## 🚀 How to Distribute to Clients

### Option 1: USB Drive
1. Copy `Clinic Management System Setup 1.0.0.exe` to a USB drive
2. Give the USB to your client
3. Client runs the installer

### Option 2: Cloud Storage
1. Upload the installer to Google Drive / OneDrive / Dropbox
2. Share the download link with your client

### Option 3: Local Network
1. Share the file on your local network
2. Client copies and runs the installer

---

## 📋 Client Installation Steps

Tell your clients to follow these steps:

1. **Run the Installer**
   - Double-click `Clinic Management System Setup 1.0.0.exe`
   - If Windows SmartScreen appears, click "More info" → "Run anyway"

2. **Choose Installation Location**
   - Default: `C:\Program Files\Clinic Management System`
   - Or choose a custom location

3. **Complete Installation**
   - Click "Install"
   - Wait for installation to complete
   - Click "Finish"

4. **Launch the Application**
   - Desktop shortcut: "Clinic Management"
   - Or Start Menu: "Clinic Management System"

---

## 🖥️ System Requirements

- **OS:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum (8GB recommended)
- **Disk Space:** 500MB free space
- **Screen:** 1366x768 minimum resolution

---

## 🌐 Network Setup (For Multi-Computer Use)

### Server Computer (Main PC with patient data)
1. Install the application
2. When prompted, select **"Run as Server"**
3. Note the IP address shown
4. Keep this computer running

### Client Computer (Reception, Pharmacy, etc.)
1. Install the application
2. When prompted, select **"Connect to Server"**
3. Enter the server's IP address
4. Click "Connect"

---

## 🔧 Troubleshooting

### "Windows protected your PC" message
- Click "More info"
- Click "Run anyway"
- This is normal for unsigned installers

### Application won't start
- Check if port 8000 is available
- Try running as Administrator
- Check Windows Firewall settings

### Can't connect to server
- Make sure server PC is running
- Both PCs must be on same network
- Check firewall allows port 8000

### Database issues
- Backup: `resources\django-app\db.sqlite3`
- Default location after install: `C:\Program Files\Clinic Management System\resources\django-app\db.sqlite3`

---

## 📁 Installed Files Location

After installation:
```
C:\Program Files\Clinic Management System\
├── Clinic Management System.exe    (Main app)
├── resources\
│   ├── django-app\                 (Backend)
│   │   ├── db.sqlite3              (Database)
│   │   ├── manage.py
│   │   └── ... (Django files)
│   └── python-portable\            (Python runtime)
```

---

## 🔄 Updating the Application

To update client installations:
1. Build a new installer with updated version
2. Client runs new installer (uninstalls old version automatically)
3. Database is preserved during update

---

## 💾 Backup Recommendations

Tell clients to regularly backup:
- `resources\django-app\db.sqlite3` - Main database
- Copy to USB or cloud storage weekly

---

## 📞 Support

For technical issues, the client should:
1. Note the error message
2. Check the log file: `%APPDATA%\Clinic Management System\electron-debug.log`
3. Contact support with these details

---

## 🔨 Rebuilding the Installer

To create a new installer after updates:

1. Run `BUILD_INSTALLER.bat`
2. Wait for build to complete
3. New installer will be in `electron\dist\`

Or manually:
```batch
cd electron
npm run build
```

---

## 📝 Version History

- **v1.0.0** - Initial release
  - Doctor Panel
  - OPD Panel  
  - Pharmacy Panel
  - Inventory Management
  - Admission Management
  - 251+ Pakistan medicines pre-loaded
