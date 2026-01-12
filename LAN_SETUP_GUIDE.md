# 🖥️ LAN Setup Guide - Clinic Management System

## Overview
This guide will help you run the clinic app on 3 laptops connected via LAN (no internet required).

---

## 🏗️ Architecture

```
┌─────────────────┐
│  SERVER LAPTOP  │ ← Runs Django + Database
│  (Main/Admin)   │
└────────┬────────┘
         │
    ┌────┴────┐ (Ethernet Cable/Switch)
    │         │
┌───┴───┐  ┌─┴─────┐
│ DOCTOR│  │  OPD  │ ← Client Laptops (Browser Only)
│LAPTOP │  │LAPTOP │    OR PHARMACY
└───────┘  └───────┘
```

---

## 📋 Requirements

### Hardware:
- 3 Laptops with Windows
- 1 Ethernet Switch/Router (OR direct Ethernet cables)
- Ethernet cables (Cat5e or Cat6)

### Software (Server Laptop Only):
- ✅ Python 3.8+ (already installed)
- ✅ Django app (already setup)
- ✅ All dependencies installed

### Software (Client Laptops):
- ✅ Any web browser (Chrome, Firefox, Edge)
- ❌ NO Python needed
- ❌ NO Django needed

---

## 🚀 Setup Instructions

### **STEP 1: Connect Laptops Physically**

**Option A: Using Network Switch (Recommended)**
```
Laptop 1 (Server) ──┐
Laptop 2 (Doctor) ──┼── Network Switch
Laptop 3 (OPD)    ──┘
```

**Option B: Direct Connection (2 laptops only)**
```
Laptop 1 ─── Ethernet Cable ─── Laptop 2
```

**Connect the cables:**
1. Plug Ethernet cables into each laptop's LAN port
2. Connect all cables to the network switch
3. Wait 10 seconds for connection

---

### **STEP 2: Configure Server Laptop**

#### 2.1 Find Server IP Address
On **SERVER LAPTOP**, open PowerShell and run:
```powershell
ipconfig
```

Look for this section:
```
Ethernet adapter Ethernet:
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
```

✅ **Note down this IP** (e.g., `192.168.1.100`)

Common IP ranges:
- `192.168.1.x`
- `192.168.0.x`
- `10.0.0.x`

#### 2.2 Configure Windows Firewall
Allow Django through firewall:

1. Open **Windows Defender Firewall**
2. Click **Advanced Settings**
3. Click **Inbound Rules** → **New Rule**
4. Choose **Port** → Next
5. Choose **TCP** → Specific port: `8000` → Next
6. Choose **Allow the connection** → Next
7. Check all profiles → Next
8. Name it: `Django Clinic App` → Finish

#### 2.3 Start Django Server
On **SERVER LAPTOP**, open PowerShell in clinic folder:

```powershell
cd "C:\Users\gh\Desktop\Clinic app"
.\env\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

✅ You should see:
```
Starting development server at http://0.0.0.0:8000/
```

**Important:** 
- `0.0.0.0:8000` means "accept connections from ANY IP"
- This allows other laptops to connect
- Keep this PowerShell window open (don't close it)

---

### **STEP 3: Configure Client Laptops**

#### 3.1 Set Static IP (Optional but Recommended)

On **EACH CLIENT LAPTOP**:

1. Open **Settings** → **Network & Internet**
2. Click **Ethernet** or **Network** 
3. Click **Change adapter options**
4. Right-click your **Ethernet** adapter → **Properties**
5. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
6. Choose **Use the following IP address:**

**Example Configuration:**
```
Server Laptop:
- IP: 192.168.1.100
- Subnet: 255.255.255.0
- Gateway: (leave blank)

Doctor Laptop:
- IP: 192.168.1.101
- Subnet: 255.255.255.0
- Gateway: (leave blank)

OPD/Pharmacy Laptop:
- IP: 192.168.1.102
- Subnet: 255.255.255.0
- Gateway: (leave blank)
```

#### 3.2 Test Connection
On **CLIENT LAPTOP**, open Command Prompt:

```cmd
ping 192.168.1.100
```

✅ Success looks like:
```
Reply from 192.168.1.100: bytes=32 time<1ms TTL=128
```

❌ Failure looks like:
```
Request timed out.
```

**Fix if ping fails:**
- Check cables are connected
- Check firewall on server laptop
- Restart network adapters

---

### **STEP 4: Access Application**

On **CLIENT LAPTOPS**, open any web browser and go to:

```
http://192.168.1.100:8000/
```

Replace `192.168.1.100` with YOUR server's IP address.

#### Login Pages:
- **Doctor Panel:** `http://192.168.1.100:8000/accounts/doctor-login/`
- **OPD Panel:** `http://192.168.1.100:8000/accounts/opd-login/`
- **Pharmacy Panel:** `http://192.168.1.100:8000/accounts/pharmacy-login/`

---

## 📌 Daily Usage Workflow

### Every Day:

1. **Server Laptop** (Admin):
   - Turn on laptop
   - Open PowerShell
   - Run: 
     ```powershell
     cd "C:\Users\gh\Desktop\Clinic app"
     .\env\Scripts\Activate.ps1
     python manage.py runserver 0.0.0.0:8000
     ```
   - Keep this running ALL DAY
   - Don't close PowerShell window

2. **Client Laptops** (Doctor, OPD, Pharmacy):
   - Turn on laptop
   - Open browser
   - Go to: `http://192.168.1.100:8000/`
   - Login and work

3. **End of Day:**
   - Close browsers on client laptops
   - Press `Ctrl+C` in PowerShell on server laptop
   - Turn off all laptops

---

## 🔧 Troubleshooting

### Problem 1: "Can't connect to server"
**Solutions:**
- Check Ethernet cables are plugged in
- Check server PowerShell is running
- Ping server IP: `ping 192.168.1.100`
- Check firewall allows port 8000
- Restart server with `0.0.0.0:8000` not `127.0.0.1:8000`

### Problem 2: "Page not loading"
**Solutions:**
- Check server PowerShell shows no errors
- Clear browser cache (Ctrl+Shift+Delete)
- Try different browser
- Check URL is correct: `http://192.168.1.100:8000/`

### Problem 3: "Database locked"
**Solutions:**
- Only happens if multiple people edit same record
- Refresh page (F5)
- Try again after 2 seconds

### Problem 4: "Changes not syncing"
**Solutions:**
- All laptops are connected to SAME server
- Database is on SERVER laptop only
- Changes are instant (no sync needed)
- Refresh page to see updates

---

## 🎯 Create Desktop Shortcuts (Optional)

### On Client Laptops:

1. Right-click Desktop → **New** → **Shortcut**
2. Enter location: `http://192.168.1.100:8000/`
3. Click **Next**
4. Name it: `Clinic App - Doctor Panel`
5. Click **Finish**
6. Right-click shortcut → **Properties**
7. Click **Change Icon** → Browse → Use browser icon
8. Click **OK**

Now double-click shortcut to open app directly!

---

## 💾 Backup Strategy

### Daily Backup:
On **SERVER LAPTOP** at end of day:

```powershell
# Copy database file
Copy-Item "C:\Users\gh\Desktop\Clinic app\db.sqlite3" -Destination "C:\Users\gh\Desktop\Backups\db_backup_$(Get-Date -Format 'yyyy-MM-dd').sqlite3"
```

### Weekly Backup:
- Copy entire `Clinic app` folder to USB drive
- Keep USB in safe place

---

## 🚨 Important Notes

### ⚠️ Security:
- This setup is for LOCAL network only
- DO NOT connect to internet with `ALLOWED_HOSTS = ['*']`
- Password protect server laptop
- Keep backups secure

### ⚠️ Performance:
- Server laptop should have:
  - At least 4GB RAM
  - Good CPU (i3 or better)
  - Keep plugged into power

### ⚠️ Reliability:
- Server laptop must stay ON during work hours
- Use UPS (backup battery) for server laptop
- Don't run heavy software on server laptop

---

## 📱 Alternative: Make Startup Automatic

Create a batch file on SERVER laptop:

1. Create file: `C:\Users\gh\Desktop\START_CLINIC_SERVER.bat`
2. Add this content:
```batch
@echo off
cd "C:\Users\gh\Desktop\Clinic app"
call .\env\Scripts\activate.bat
python manage.py runserver 0.0.0.0:8000
pause
```
3. Double-click this file to start server instead of typing commands

---

## ✅ Quick Reference

| Laptop | Role | Needs Django? | Access Via |
|--------|------|---------------|------------|
| Server | Main/Admin | ✅ Yes | PowerShell |
| Doctor | Client | ❌ No | Browser |
| OPD/Pharmacy | Client | ❌ No | Browser |

**Server Command:**
```powershell
python manage.py runserver 0.0.0.0:8000
```

**Client URL:**
```
http://192.168.1.100:8000/
```

**Default Ports:**
- Django: `8000`
- Firewall: Allow TCP 8000

---

## 🎉 You're Done!

Your clinic app is now running on local network without internet!

**Questions?**
- Test connectivity: `ping 192.168.1.100`
- Check server: PowerShell should show activity
- Check clients: Browser should load page

**Need Help?**
1. Check this guide step by step
2. Verify all cables connected
3. Confirm server is running
4. Test ping between laptops
