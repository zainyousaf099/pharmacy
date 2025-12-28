# Quick Start Instructions

## For SERVER Laptop (Main Computer):

1. **Double-click:** `START_SERVER.bat`
2. **Wait** for message: "Starting development server at http://0.0.0.0:8000/"
3. **Find your IP:**
   - Open another PowerShell
   - Type: `ipconfig`
   - Look for IPv4 Address (e.g., 192.168.1.100)
4. **Keep window open** all day

## For CLIENT Laptops (Doctor, OPD, Pharmacy):

1. **Open browser** (Chrome, Firefox, Edge)
2. **Type in address bar:** `http://192.168.1.100:8000/`
   (Replace `192.168.1.100` with server's IP)
3. **Login** to your panel
4. **Work normally**

## Connection Setup:

```
Connect Ethernet cables like this:

SERVER LAPTOP
    |
    | (Ethernet Cable)
    |
NETWORK SWITCH
    |
    |--- DOCTOR LAPTOP
    |--- OPD LAPTOP (or PHARMACY)
```

## Firewall Setup (One-time):

On SERVER laptop:
1. Windows Search → "Windows Defender Firewall"
2. Advanced Settings → Inbound Rules → New Rule
3. Port → TCP → 8000 → Allow → Name: Django

## That's it!

✅ No internet needed
✅ Fast local network
✅ All data on server laptop
✅ Other laptops just use browser

---

## Troubleshooting:

**Can't connect?**
- Check cables plugged in
- Ping server: `ping 192.168.1.100`
- Check firewall allows port 8000
- Server bat file should be running

**Need help?**
Read full guide: `LAN_SETUP_GUIDE.md`
