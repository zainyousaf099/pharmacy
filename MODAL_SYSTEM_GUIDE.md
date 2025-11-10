# Universal Modal System - Developer Guide

## Overview
The Universal Modal System is a modern, professional popup/modal component built into the `base.html` template. It replaces default browser `alert()`, `confirm()`, and `prompt()` dialogs with beautiful, animated modals.

## Features
- ✅ Modern glassmorphism design with backdrop blur
- ✅ Smooth animations and transitions
- ✅ Multiple modal types (success, error, warning, info, confirm)
- ✅ Auto-dismiss capability
- ✅ Loading spinner for async operations
- ✅ Custom buttons and callbacks
- ✅ Input prompts
- ✅ Globally accessible across all pages
- ✅ Mobile responsive

## Usage

### Basic Methods

#### 1. Success Message
```javascript
Modal.success('Operation completed!', 'Success', 3000);
// Parameters: message, title (optional), autoDismiss time in ms (optional)
```

#### 2. Error Message
```javascript
Modal.error('Something went wrong!', 'Error');
// Parameters: message, title (optional), autoDismiss time (optional, default: 0)
```

#### 3. Warning Message
```javascript
Modal.warning('Please check your input!', 'Warning');
// Parameters: message, title (optional), autoDismiss time (optional)
```

#### 4. Info Message
```javascript
Modal.info('This is an informational message.', 'Information');
// Parameters: message, title (optional), autoDismiss time (optional)
```

#### 5. Confirm Dialog
```javascript
Modal.confirm(
    'Are you sure you want to delete this item?',
    () => {
        // User clicked Confirm
        console.log('Confirmed!');
    },
    () => {
        // User clicked Cancel
        console.log('Cancelled');
    },
    'Confirm Action'  // Title (optional)
);
```

#### 6. Loading Spinner
```javascript
// Show loading
Modal.loading('Processing...', 'Please Wait');

// Close when done
Modal.close();
```

#### 7. Prompt (Input Dialog)
```javascript
Modal.prompt(
    'Enter your name:',
    (value) => {
        console.log('User entered:', value);
    },
    'John Doe',  // Default value (optional)
    'Name Required'  // Title (optional)
);
```

### Advanced Usage

#### Custom Modal with Buttons
```javascript
Modal.show({
    type: 'info',  // success, error, warning, info, confirm
    title: 'Custom Modal',
    message: 'This is a custom modal with multiple buttons.',
    buttons: [
        {
            text: 'Option 1',
            style: 'primary',  // primary, success, danger, secondary
            onClick: () => {
                console.log('Option 1 clicked');
                Modal.close();
            }
        },
        {
            text: 'Option 2',
            style: 'success',
            onClick: () => {
                console.log('Option 2 clicked');
                Modal.close();
            }
        },
        {
            text: 'Cancel',
            style: 'secondary',
            onClick: () => Modal.close()
        }
    ],
    autoDismiss: 5000,  // Auto close after 5 seconds
    onClose: (returnValue) => {
        console.log('Modal closed with:', returnValue);
    }
});
```

#### HTML Content Support
```javascript
Modal.success(
    '<strong>Success!</strong><br>Your changes have been saved.<br><small>Reference ID: 12345</small>',
    'Operation Complete',
    3000
);
```

## Real-World Examples

### Example 1: Form Validation
```javascript
function validateForm() {
    const name = document.getElementById('name').value;
    
    if (!name) {
        Modal.warning('Please enter your name!', 'Validation Error');
        return false;
    }
    
    return true;
}
```

### Example 2: AJAX Request with Loading
```javascript
function saveData() {
    // Show loading
    Modal.loading('Saving your data...', 'Please Wait');
    
    fetch('/api/save', {
        method: 'POST',
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        Modal.close();  // Close loading
        
        if (data.success) {
            Modal.success('Data saved successfully!', 'Success', 2000);
        } else {
            Modal.error('Failed to save: ' + data.error, 'Error');
        }
    })
    .catch(error => {
        Modal.close();  // Close loading
        Modal.error('Connection error. Please try again.', 'Network Error');
    });
}
```

### Example 3: Delete Confirmation
```javascript
function deleteItem(itemId, itemName) {
    Modal.confirm(
        `Are you sure you want to delete <strong>"${itemName}"</strong>?<br><br>This action cannot be undone.`,
        () => {
            // User confirmed
            Modal.loading('Deleting...', 'Please Wait');
            
            fetch(`/api/delete/${itemId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                Modal.close();
                
                if (data.success) {
                    Modal.success('Item deleted successfully!', 'Deleted', 2000);
                    setTimeout(() => location.reload(), 2000);
                } else {
                    Modal.error('Delete failed: ' + data.error, 'Error');
                }
            })
            .catch(error => {
                Modal.close();
                Modal.error('Failed to delete. Please try again.', 'Error');
            });
        },
        null,  // No cancel callback needed
        'Confirm Deletion'
    );
}
```

### Example 4: Sequential Operations
```javascript
async function processMultipleSteps() {
    Modal.loading('Step 1: Validating...', 'Processing');
    await validateData();
    
    Modal.loading('Step 2: Uploading...', 'Processing');
    await uploadFiles();
    
    Modal.loading('Step 3: Finalizing...', 'Processing');
    await finalize();
    
    Modal.close();
    Modal.success('All steps completed successfully!', 'Done', 3000);
}
```

## Styling

### Modal Types and Colors
- **Success**: Green gradient (`#4CAF50` → `#45a049`)
- **Error**: Red gradient (`#f44336` → `#d32f2f`)
- **Warning**: Orange gradient (`#ff9800` → `#f57c00`)
- **Info**: Blue gradient (`#2196F3` → `#1976D2`)
- **Confirm**: Purple gradient (`#9c27b0` → `#7b1fa2`)

### Button Styles
- **primary**: Blue gradient
- **success**: Green gradient
- **danger**: Red gradient
- **secondary**: Gray gradient

## Browser Compatibility
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## Keyboard Shortcuts
- **ESC**: Close modal
- **Enter**: Submit prompt input

## Best Practices

1. **Use appropriate types**: Match the modal type to the message (success for success, error for errors, etc.)

2. **Keep messages concise**: Short, clear messages are more effective

3. **Use auto-dismiss for success**: Success messages can auto-dismiss after 2-3 seconds
   ```javascript
   Modal.success('Saved!', 'Success', 2000);
   ```

4. **Don't auto-dismiss errors**: Let users read error messages
   ```javascript
   Modal.error('Error occurred', 'Error');  // No auto-dismiss
   ```

5. **Show loading for async operations**: Always show loading during network requests
   ```javascript
   Modal.loading('Processing...');
   // ... async operation ...
   Modal.close();
   ```

6. **Use HTML for formatting**: Make important text bold, use line breaks
   ```javascript
   Modal.info('<strong>Important:</strong><br>Please read carefully.');
   ```

7. **Provide clear actions**: Use descriptive button text
   ```javascript
   buttons: [
       { text: 'Delete Permanently', style: 'danger', onClick: deleteAction },
       { text: 'Keep It', style: 'secondary', onClick: cancelAction }
   ]
   ```

## Migration from Default Dialogs

### Before (Old Way)
```javascript
alert('Message');
if (confirm('Are you sure?')) {
    doSomething();
}
var name = prompt('Enter name:');
```

### After (New Way)
```javascript
Modal.info('Message');
Modal.confirm('Are you sure?', () => {
    doSomething();
});
Modal.prompt('Enter name:', (name) => {
    console.log(name);
});
```

## Troubleshooting

**Modal not showing?**
- Ensure page has loaded (`DOMContentLoaded` event)
- Check browser console for errors
- Verify `base.html` is extended properly

**Modal stuck open?**
- Call `Modal.close()` explicitly
- Check for JavaScript errors preventing execution

**Buttons not working?**
- Ensure onClick callbacks call `Modal.close()` when needed
- Check console for callback errors

## Future Enhancements
- [ ] Toast notifications (corner popups)
- [ ] Multiple modals stacking
- [ ] Animation options
- [ ] Custom themes
- [ ] Progress bars
- [ ] Rich content (images, videos)

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Integrated**: All templates extending `base.html`
