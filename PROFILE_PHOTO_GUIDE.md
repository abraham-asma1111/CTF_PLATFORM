# Profile Photo & Edit Profile Guide

## Overview
Users can now upload profile photos and edit their profile information including bio, personal details, and more.

## Features

### 1. Profile Photo Upload
- Upload profile pictures (JPG, PNG, GIF)
- Maximum file size: 5MB
- Automatic image preview before upload
- Circular display with border
- Default avatar icon if no photo uploaded

### 2. Profile Editing
- Edit first name and last name
- Add/edit bio (up to 500 characters)
- Update sex, education level, department
- Email is read-only for security

### 3. Profile Display
- Photo shown in navbar
- Photo shown in profile card
- Bio displayed on profile page
- Edit button for quick access

## User Flow

### Upload Profile Photo

1. Go to your profile page
2. Click "✏️ Edit Profile" button
3. Click on the profile photo input
4. Select an image file (max 5MB)
5. Preview appears immediately
6. Click "Save Changes"
7. Photo is uploaded and displayed

### Edit Profile Information

1. Navigate to profile page
2. Click "✏️ Edit Profile"
3. Update any fields:
   - First Name
   - Last Name
   - Bio
   - Sex
   - Education Level
   - Department
4. Click "Save Changes"
5. Redirected to profile page with success message

## Technical Details

### Database Schema

#### UserProfile Model
```python
profile_photo = ImageField(upload_to='profile_photos/', null=True, blank=True)
bio = TextField(max_length=500, null=True, blank=True)
```

### File Storage
- Photos stored in: `media/profile_photos/`
- Served at: `/media/profile_photos/`
- Automatic filename generation by Django

### Form Validation
- Image file type validation
- File size limit: 5MB
- Bio character limit: 500
- Email field disabled (cannot be changed)

## Configuration

### Settings (ctf_platform/settings.py)
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### URLs (ctf_platform/urls.py)
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Security Considerations

### File Upload Security
1. **File Type Validation** - Only images allowed
2. **File Size Limit** - Maximum 5MB
3. **Secure Storage** - Files stored outside web root
4. **Unique Filenames** - Django generates unique names
5. **Access Control** - Only authenticated users can upload

### Email Protection
- Email field is read-only in edit form
- Prevents unauthorized email changes
- Maintains account security

### Input Validation
- Bio limited to 500 characters
- Name fields validated
- CSRF protection on all forms

## File Structure

```
media/
└── profile_photos/
    ├── user1_photo.jpg
    ├── user2_photo.png
    └── ...

templates/users/
├── profile.html (updated with photo display)
└── edit_profile.html (new)

users/
├── models.py (added profile_photo, bio fields)
├── forms.py (added ProfileEditForm)
├── views.py (added edit_profile view)
└── urls.py (added edit_profile route)
```

## Usage Examples

### Access Edit Profile
```
URL: /users/profile/edit/
Method: GET, POST
Login Required: Yes
```

### Upload Photo via Form
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form.profile_photo }}
    <button type="submit">Upload</button>
</form>
```

### Display Photo in Template
```html
{% if profile.profile_photo %}
    <img src="{{ profile.profile_photo.url }}" alt="Profile">
{% else %}
    <span>👤</span>
{% endif %}
```

## Troubleshooting

### Photo Not Uploading
- Check file size (must be < 5MB)
- Verify file type (JPG, PNG, GIF only)
- Ensure `enctype="multipart/form-data"` in form
- Check media directory permissions

### Photo Not Displaying
- Verify MEDIA_URL and MEDIA_ROOT in settings
- Check that media URLs are configured
- Ensure DEBUG=True or configure static file serving
- Check file exists in media/profile_photos/

### Permission Errors
```bash
# Fix media directory permissions
chmod 755 media/
chmod 755 media/profile_photos/
```

### Missing Pillow Library
```bash
pip install Pillow
```

## Best Practices

### For Users
1. Use square images for best results
2. Keep file size reasonable (< 2MB recommended)
3. Use clear, professional photos
4. Update bio to introduce yourself
5. Keep profile information current

### For Administrators
1. Monitor media directory size
2. Implement cleanup for deleted users
3. Consider image optimization
4. Set up CDN for production
5. Regular backups of media files

## Production Deployment

### Media File Serving
For production, use a proper web server or CDN:

#### Option 1: Nginx
```nginx
location /media/ {
    alias /path/to/media/;
}
```

#### Option 2: AWS S3
```python
# Install django-storages
pip install django-storages boto3

# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'
```

#### Option 3: Cloudinary
```python
# Install cloudinary
pip install cloudinary

# settings.py
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'your-cloud-name',
    'API_KEY': 'your-api-key',
    'API_SECRET': 'your-api-secret'
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

## Image Optimization

### Automatic Resize (Optional)
Add to models.py:
```python
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

def save(self, *args, **kwargs):
    if self.profile_photo:
        img = Image.open(self.profile_photo)
        
        # Resize to 300x300
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            
            # Save to BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            # Replace file
            self.profile_photo = InMemoryUploadedFile(
                output, 'ImageField',
                f"{self.profile_photo.name.split('.')[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
    
    super().save(*args, **kwargs)
```

## API Endpoints

### Edit Profile
- **URL**: `/users/profile/edit/`
- **Method**: GET, POST
- **Auth**: Required
- **Parameters**:
  - `profile_photo` (file)
  - `bio` (text)
  - `first_name` (text)
  - `last_name` (text)
  - `sex` (choice)
  - `education_level` (choice)
  - `department` (choice)

## Testing

### Test Photo Upload
```python
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

class ProfilePhotoTest(TestCase):
    def test_upload_photo(self):
        # Create test image
        image = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        # Upload
        response = self.client.post('/users/profile/edit/', {
            'profile_photo': image
        })
        
        self.assertEqual(response.status_code, 302)
```

## Maintenance

### Clean Up Old Photos
```python
# management/commands/cleanup_photos.py
from django.core.management.base import BaseCommand
from users.models import UserProfile
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get all photo paths from database
        db_photos = set(UserProfile.objects.exclude(
            profile_photo=''
        ).values_list('profile_photo', flat=True))
        
        # Get all files in directory
        photo_dir = 'media/profile_photos/'
        for filename in os.listdir(photo_dir):
            filepath = f'profile_photos/{filename}'
            if filepath not in db_photos:
                os.remove(os.path.join(photo_dir, filename))
                self.stdout.write(f'Deleted: {filename}')
```

## Current Status

✅ Profile photo upload implemented
✅ Image preview before upload
✅ File size and type validation
✅ Profile edit page created
✅ Bio field added
✅ Photo display in navbar and profile
✅ Edit button on profile page
✅ Form validation and error handling
✅ Media file configuration
✅ Migrations applied

**System is ready for profile photo uploads!**
