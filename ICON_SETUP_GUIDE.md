# ICON SETUP INSTRUCTIONS

## 🎨 Adding Icon to .exe File

### Current Status:
- Icon image provided by user (medical heart with stethoscope)
- Need to convert to .ico format

### Steps to Add Icon:

#### Method 1: Use Online Converter (Easiest)

1. Save the icon image you provided
2. Go to: https://convertio.co/png-ico/
3. Upload your icon image
4. Convert to .ico format
5. Download the .ico file
6. Save it as: `C:\Users\gh\Desktop\Clinic app\electron\icon.ico`
7. Rebuild the app: `npm run build-win`

#### Method 2: Use Windows Built-in Tool

1. Open your icon image in Paint
2. File → Save As → Other Formats
3. Choose .ico format (if available)
4. Save as: `C:\Users\gh\Desktop\Clinic app\electron\icon.ico`
5. Rebuild the app: `npm run build-win`

#### Method 3: Use IcoFX or GIMP

1. Install IcoFX (free) or GIMP (free)
2. Open your icon image
3. Resize to 256x256 pixels
4. Export/Save as .ico format
5. Save as: `C:\Users\gh\Desktop\Clinic app\electron\icon.ico`
6. Rebuild the app

---

## ✅ After Saving icon.ico:

Run this command to rebuild with new icon:

```powershell
cd "C:\Users\gh\Desktop\Clinic app\electron"
npm run build-win
```

The icon will appear on:
- ✅ Desktop shortcut
- ✅ Taskbar
- ✅ Start menu
- ✅ File explorer
- ✅ Alt+Tab switcher

---

## 📁 Icon Location:

**Must be:** `C:\Users\gh\Desktop\Clinic app\electron\icon.ico`

The package.json is already configured to use this icon:
```json
"win": {
  "icon": "icon.ico"
}
```

---

## 🔧 Troubleshooting:

**Icon not showing after build:**
- Make sure icon.ico exists in electron folder
- Icon must be in .ico format (not .png or .jpg)
- Rebuild the app completely
- Windows may cache old icon - restart Explorer or reboot

**Icon quality issues:**
- Use at least 256x256 pixels
- .ico files can contain multiple sizes (16, 32, 48, 256)
- Higher resolution = better quality

---

## Current Setup:

File already configured in package.json:
```json
"files": [
  "main.js",
  "preload.js",
  "renderer.js",
  "index.html",
  "styles.css",
  "icon.ico",           ← Already here!
  "network-discovery.js",
  "django-app/**/*"
],
"win": {
  "target": "nsis",
  "icon": "icon.ico"    ← Already configured!
}
```

Just need to:
1. Convert your image to icon.ico
2. Place in electron folder
3. Rebuild!
