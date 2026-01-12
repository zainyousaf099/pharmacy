# 🏥 3-LAPTOP SETUP GUIDE

## Overview
One laptop = SERVER (database)
Other laptops = CLIENTS (connect to server)
All use the SAME database!

---

## 📋 STEP 1: Setup Server Laptop

**Choose ONE laptop to be the server** (usually OPD or most reliable)

1. Copy the entire project folder to server laptop
2. Double-click: **SETUP_AS_SERVER.bat**
3. Note the IP address shown (e.g., 192.168.1.100)
4. Write it down - you'll need it for other laptops!
5. Run: **RUN_DESKTOP_APP.bat** or the built .exe

✅ Server laptop is ready!

---

## 📋 STEP 2: Setup Client Laptops (Doctor & Pharmacy)

**On EACH client laptop:**

1. Copy the entire project folder
2. Double-click: **SETUP_AS_CLIENT.bat**
3. Enter the server IP you wrote down (e.g., 192.168.1.100)
4. Press Enter
5. Run: **RUN_DESKTOP_APP.bat** or the built .exe

✅ Client laptops are ready!

---

## 🌐 Network Connection

Connect all 3 laptops using ONE of these methods:

### Option A: WiFi (Easiest)
- Connect all 3 laptops to the SAME WiFi network
- That's it!

### Option B: Ethernet Cables
- Get 1 network switch/router
- Connect all 3 laptops to the switch with cables
- Or connect 2 laptops directly to 1 laptop (if it has multiple ports)

---

## 🔥 How It Works

### Server Laptop (e.g., OPD):
```
✅ Starts Django server
✅ Hosts the database (db.sqlite3)
✅ Shows role selection screen in desktop app
✅ All changes are saved here
```

### Client Laptops (Doctor & Pharmacy):
```
✅ NO Django server started
✅ NO separate database created
✅ Shows role selection screen in desktop app
✅ Connects to server laptop's database
✅ All changes go to server's database
```

---

## 📝 Daily Usage

### Morning (Starting Work):

1. **Start Server Laptop First**
   - Turn on the server laptop
   - Run the desktop app
   - Wait for role selection screen

2. **Start Client Laptops**
   - Turn on doctor & pharmacy laptops
   - Run desktop app on each
   - They'll connect to server automatically

### During Work:
- OPD registers patient → Saved to server database
- Doctor sees patient immediately in their list
- Doctor writes prescription → Saved to server
- Pharmacy sees prescription immediately
- All working on SAME data!

### Evening (Closing):
- Close desktop app on all laptops
- Server laptop can be shut down last

---

## 🔧 Configuration Files

### config.json (Auto-created by setup scripts)

**Server mode:**
```json
{
  "mode": "server",
  "serverIP": "localhost"
}
```

**Client mode:**
```json
{
  "mode": "client",
  "serverIP": "192.168.1.100"
}
```

---

## ⚠️ Troubleshooting

### "Cannot connect to server"
- Check if server laptop is ON
- Check if server laptop app is running
- Verify all laptops on same network
- Ping server IP from client: `ping 192.168.1.100`

### "Slow performance"
- Check WiFi signal strength
- Try Ethernet cables instead
- Restart server laptop

### "Different data showing"
- Check config.json - make sure clients point to correct server IP
- Re-run SETUP_AS_CLIENT.bat and enter correct IP

### Change Server Laptop
- Run SETUP_AS_SERVER.bat on new laptop
- Note new IP address
- Run SETUP_AS_CLIENT.bat on all other laptops with new IP

---

## 📊 Current Configuration

**Server Laptop:** Not configured yet
**Server IP:** Will be shown after running SETUP_AS_SERVER.bat

**Laptop 1 (Server):** Run SETUP_AS_SERVER.bat
**Laptop 2 (Client):** Run SETUP_AS_CLIENT.bat  
**Laptop 3 (Client):** Run SETUP_AS_CLIENT.bat

---

## ✅ Verification Steps

After setup, verify everything works:

1. **On Server Laptop:**
   - Open app → Role selection appears
   - Select OPD → Register a test patient
   - Note the patient reference number

2. **On Doctor Laptop:**
   - Open app → Role selection appears
   - Select Doctor → Login
   - Search for the patient you just created
   - Should find it immediately!

3. **Test Prescription:**
   - Doctor writes prescription
   - Pharmacy laptop should see it in their queue

✅ If all above works → Setup is perfect!

---

## 📞 Quick Reference

| Laptop | Role | Setup Command | Database |
|--------|------|---------------|----------|
| Laptop 1 | Server | SETUP_AS_SERVER.bat | ✅ Has DB |
| Laptop 2 | Client | SETUP_AS_CLIENT.bat | ❌ Uses Server |
| Laptop 3 | Client | SETUP_AS_CLIENT.bat | ❌ Uses Server |

**Remember:** Only ONE laptop runs as server. Others are clients!
