# Django Admin Panel Access Guide

## 🔑 Step 1: Create Admin Account (One Time Only)

### Open Terminal/PowerShell and run:

```powershell
cd "C:\Users\gh\Desktop\Clinic app"
.\env\Scripts\activate
python manage.py createsuperuser
```

### You'll be asked:
1. **Username:** Enter admin username (e.g., `admin`)
2. **Email:** Enter email (can leave blank, just press Enter)
3. **Password:** Enter strong password
4. **Password confirmation:** Enter same password again

### Example:
```
Username: admin
Email address: admin@clinic.com
Password: ********
Password (again): ********
Superuser created successfully!
```

---

## 🌐 Step 2: Access Admin Panel

### When Desktop App is Running:

**Method 1: Add to App Menu**
- Admin panel will be accessible from app sidebar
- Or open browser and go to: `http://localhost:8000/admin/`

**Method 2: Direct Browser Access**
- If you're the SERVER laptop: `http://localhost:8000/admin/`
- If you're CLIENT laptop: `http://SERVER_IP:8000/admin/`
  (Replace SERVER_IP with actual server IP)

### Login:
- Username: (the one you created above)
- Password: (the password you set)

---

## 📊 What You Can Do in Admin Panel:

✅ **User Management:**
- Add/edit/delete staff users
- Manage permissions
- Reset passwords

✅ **View All Data:**
- All patients
- All prescriptions
- All admissions
- Inventory items
- Expenses

✅ **Reports & Analytics:**
- Patient statistics
- Medicine usage
- Financial reports

✅ **System Configuration:**
- Manage medicine templates
- Configure room/bed assignments
- Set up distributors

---

## 🔐 Security:

- Only create admin account on SERVER laptop
- Don't share admin credentials with regular users
- Admin has full access to all data
- Can delete/modify anything!

---

## 🚀 Quick Access from Desktop App

### Option 1: Add Admin Link to Sidebar

I can add "Admin Panel" link to the hamburger menu in all panels.

### Option 2: Browser Bookmark

Just bookmark `http://localhost:8000/admin/` in your browser for quick access.

---

## ⚙️ Admin Panel Features:

1. **Accounts** - Staff users, roles
2. **Admission** - Admitted patients, rooms, beds
3. **Doctor** - Prescription templates, medicines
4. **Inventory** - Products, expenses, distributors
5. **OPD** - Patient records
6. **Pharmacy** - Prescriptions (view only)

---

## 📝 First Time Setup Checklist:

After creating superuser:
1. ✅ Login to admin panel
2. ✅ Add staff users (Doctor, OPD, Pharmacy)
3. ✅ Set up rooms and beds
4. ✅ Add medicine templates
5. ✅ Add inventory items
6. ✅ Add distributors (if using inventory)

---

## 🔥 Pro Tips:

- Use admin panel for bulk operations
- Export data using Django admin actions
- Regular users don't need admin access
- Keep admin password secure and complex!

**Default URL:** `http://localhost:8000/admin/`
