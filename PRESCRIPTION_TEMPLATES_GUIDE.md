# Prescription Template System - User Guide

## Overview
The Prescription Template System allows doctors to create reusable prescription templates for common conditions (e.g., Headache, Stomach Pain, Fever). These templates can be quickly loaded into the prescription form, saving time and reducing repetitive data entry.

## Features

### 1. **Create Templates**
- Navigate to **Doctor Panel** → **Manage Templates** → **Create Template**
- Provide a **name** (e.g., "Headache Treatment")
- Add a **description** (optional, explains when to use this template)
- Add **multiple medicines** with:
  - Medicine name (searchable autocomplete)
  - Duration (1-30 days)
  - Timing (Morning, Evening, Night checkboxes)
- Click **Save Template**

### 2. **View Templates**
- Navigate to **Doctor Panel** → **Manage Templates**
- See all created templates with:
  - Template name
  - Description
  - Number of medicines
  - Creation date
- Click **View** to see template details
- Click **Delete** to remove templates

### 3. **Use Templates in Prescriptions**
- In the **Doctor Dashboard**, find the **Load Template** dropdown at the top
- Select a template from the dropdown
- Click **Load** button
- All medicines from the template will automatically populate the prescription table
- Review and modify if needed
- Search and select patient
- Click **Save & Print** to complete

## How It Works

### Backend Structure

**Models** (`doctor/models.py`):
- `PrescriptionTemplate`: Stores template name, description, created_by, and timestamps
- `PrescriptionTemplateMedicine`: Links medicines to templates with dosage details (days, morning/evening/night timing, notes, order)

**Views** (`doctor/views.py`):
- `template_list`: Display all templates
- `template_create`: Create new template
- `template_detail`: View template details
- `template_delete`: Delete a template
- `get_all_templates_api`: API to fetch templates for dropdown
- `get_template_medicines_api`: API to fetch medicines of a specific template

**URLs** (`doctor/urls.py`):
```python
/doctor/templates/                          # List all templates
/doctor/templates/create/                   # Create new template
/doctor/templates/<uuid>/                   # View template details
/doctor/templates/<uuid>/delete/            # Delete template
/doctor/api/templates/                      # API: Get all templates
/doctor/api/templates/<uuid>/medicines/     # API: Get template medicines
```

### Frontend Files

**Templates**:
- `templates/doctortemp/templates_list.html`: Template management page
- `templates/doctortemp/template_create.html`: Template creation form
- `templates/doctortemp/template_detail.html`: Template details view
- `templates/doctortemp/dashboard.html`: Updated with template dropdown

**JavaScript Flow**:
1. Page loads → Fetch all templates via API
2. Populate dropdown with template names
3. User selects template → Click "Load" button
4. Fetch template medicines via API
5. Clear existing prescription rows
6. Create new rows for each template medicine
7. Pre-fill medicine name, days, and timing checkboxes
8. Initialize autocomplete for medicine search

## Admin Interface

Templates can also be managed via Django Admin:
- Navigate to `/admin/`
- Find **Doctor → Prescription Templates**
- Create, edit, or delete templates
- Inline editing of medicines within templates

## Example Use Case

**Scenario**: Common headache patients visit daily

**Solution**:
1. Create template "Headache Treatment" with medicines:
   - Paracetamol 500mg - 3 days - Morning, Evening, Night
   - Ibuprofen 400mg - 2 days - Evening, Night

2. When a headache patient arrives:
   - Open Doctor Dashboard
   - Select "Headache Treatment" from dropdown
   - Click "Load"
   - Medicines auto-fill instantly
   - Search patient
   - Save & Print

**Time Saved**: 2-3 minutes per prescription ✓

## Benefits

✅ **Speed**: Load common prescriptions in 1 click  
✅ **Consistency**: Standardized treatments for common conditions  
✅ **Accuracy**: Reduce manual entry errors  
✅ **Flexibility**: Edit loaded medicines before saving  
✅ **Reusability**: Create once, use unlimited times  

## Tips

- Create templates for your most common patient conditions
- Use descriptive names (e.g., "Child Fever Protocol", "Adult Headache")
- Add helpful descriptions to remember when to use each template
- Update templates via Admin panel when treatment protocols change
- Review loaded medicines before saving prescription

## Technical Details

- **Database**: SQLite with UUID primary keys
- **Backend**: Django 4.2 with REST-like API endpoints
- **Frontend**: Vanilla JavaScript with Fetch API
- **Design**: Modern glassmorphism with red gradient theme
- **Autocomplete**: Real-time medicine search with dropdown
- **Responsive**: Works on all screen sizes

## Troubleshooting

**Template not loading?**
- Check browser console for errors
- Ensure template has at least 1 medicine
- Verify internet connection

**Medicines not appearing?**
- Refresh page and try again
- Check if template was saved correctly in Admin

**Can't delete template?**
- Ensure you have proper permissions
- Check if template is in use (shouldn't prevent deletion)

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Developed for**: Clinic Management System
