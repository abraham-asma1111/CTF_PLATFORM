# reCAPTCHA Setup Guide for CTF Platform

## Overview
This guide explains how to set up Google reCAPTCHA v2 for the registration page to prevent bot registrations.

## Step 1: Get reCAPTCHA Keys

1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click on the **+** button to create a new site
3. Fill in the form:
   - **Label**: CTF Platform (or any name you prefer)
   - **reCAPTCHA type**: Select **reCAPTCHA v2** → **"I'm not a robot" Checkbox**
   - **Domains**: Add your domains:
     - For local development: `localhost` or `127.0.0.1`
     - For production: `yourdomain.com`
   - Accept the reCAPTCHA Terms of Service
4. Click **Submit**
5. You'll receive two keys:
   - **Site Key** (Public Key) - Used in the frontend
   - **Secret Key** (Private Key) - Used in the backend

## Step 2: Configure Environment Variables

Add your reCAPTCHA keys to the `.env` file:

```bash
# reCAPTCHA Configuration
RECAPTCHA_PUBLIC_KEY=your-site-key-here
RECAPTCHA_PRIVATE_KEY=your-secret-key-here
```

Replace `your-site-key-here` and `your-secret-key-here` with the actual keys from Step 1.

## Step 3: Test the Configuration

1. Restart your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the registration page: `http://localhost:8000/users/register/`

3. You should see the reCAPTCHA checkbox at the bottom of the form

4. Try to register:
   - Without checking the box → Should show an error
   - With checking the box → Should proceed normally

## Development vs Production

### Development (localhost)
- reCAPTCHA works on localhost without any special configuration
- Make sure to add `localhost` or `127.0.0.1` to your domains in the reCAPTCHA admin console

### Production
- Add your actual domain (e.g., `ctfplatform.com`) to the reCAPTCHA admin console
- Update the `.env` file on your production server with the same keys
- reCAPTCHA will automatically work on your production domain

## Testing Keys (For Development Only)

Google provides test keys that always pass validation:

```bash
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```

**Warning**: These keys should NEVER be used in production!

## Troubleshooting

### reCAPTCHA not showing
- Check that `django_recaptcha` is in `INSTALLED_APPS` in `settings.py`
- Verify that your keys are correctly set in `.env`
- Make sure you restarted the Django server after adding the keys

### "Invalid site key" error
- Verify that the domain in your browser matches the domains configured in reCAPTCHA admin
- For localhost, make sure you added `localhost` or `127.0.0.1` to allowed domains

### "ERROR for site owner: Invalid domain for site key"
- The domain you're accessing doesn't match the domains configured in reCAPTCHA admin
- Add the domain to your reCAPTCHA site configuration

### reCAPTCHA validation always fails
- Check that `RECAPTCHA_PRIVATE_KEY` is correct in `.env`
- Verify that the secret key matches the site key
- Make sure you're not using test keys in production

## Security Best Practices

1. **Never commit keys to version control** - Always use environment variables
2. **Use different keys for development and production**
3. **Rotate keys periodically** - Generate new keys every few months
4. **Monitor reCAPTCHA analytics** - Check the admin console for suspicious activity
5. **Keep django-recaptcha updated** - Run `pip install --upgrade django-recaptcha`

## Additional Configuration

### Customize reCAPTCHA Theme

In `settings.py`, you can customize the reCAPTCHA appearance:

```python
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', '')

# Optional: Customize widget attributes
RECAPTCHA_WIDGET_ATTRS = {
    'data-theme': 'dark',  # 'light' or 'dark'
    'data-size': 'normal',  # 'normal' or 'compact'
}
```

### Using reCAPTCHA v3 (Score-based)

If you prefer invisible reCAPTCHA v3:

1. Create a new reCAPTCHA v3 site in the admin console
2. Update `users/forms.py`:
   ```python
   from django_recaptcha.fields import ReCaptchaField
   from django_recaptcha.widgets import ReCaptchaV3
   
   class CustomUserCreationForm(UserCreationForm):
       captcha = ReCaptchaField(widget=ReCaptchaV3)
   ```
3. Set the required score in `settings.py`:
   ```python
   RECAPTCHA_REQUIRED_SCORE = 0.85
   ```

## Resources

- [Google reCAPTCHA Documentation](https://developers.google.com/recaptcha)
- [django-recaptcha Documentation](https://github.com/torchbox/django-recaptcha)
- [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)

## Current Status

✅ reCAPTCHA v2 is configured and ready to use
✅ Registration form includes reCAPTCHA validation
✅ Environment variables are set up in `.env`
✅ Test keys are available for development

**Next Steps**: Get your production keys from Google reCAPTCHA admin console and update the `.env` file.
