# 📧 Gmail App Password Setup Guide

## 🎯 Quick Fix for Email Authentication

The FinSolve AI Assistant email service requires a **Gmail App Password** instead of your regular Gmail password for security reasons.

---

## 📋 **Step-by-Step Setup**

### **Step 1: Enable 2-Factor Authentication**

1. **Go to Google Account Security**:
   - Visit: https://myaccount.google.com/security
   - Sign in with your Gmail account (keyegon@gmail.com)

2. **Enable 2-Step Verification**:
   - Under "Signing in to Google", click **2-Step Verification**
   - Follow the prompts to set up 2FA (if not already enabled)
   - You can use SMS, Google Authenticator, or other methods

### **Step 2: Generate App Password**

1. **Access App Passwords**:
   - Go to: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → App passwords

2. **Create New App Password**:
   - Click **Select app** → Choose **Mail**
   - Click **Select device** → Choose **Other (Custom name)**
   - Enter: `FinSolve AI Assistant`
   - Click **Generate**

3. **Copy the App Password**:
   - You'll see a 16-character password like: `abcd efgh ijkl mnop`
   - **Copy this password** (remove spaces when using)

### **Step 3: Update .env File**

1. **Open the .env file** in the DS-RPC-01 directory

2. **Replace the EMAIL_PASSWORD line**:
   ```env
   # Change this:
   EMAIL_PASSWORD=your_gmail_app_password_here
   
   # To this (using your actual app password):
   EMAIL_PASSWORD=abcdefghijklmnop
   ```

3. **Save the file**

---

## 🧪 **Test the Configuration**

After updating the .env file, run the test again:

```bash
python test_email.py
```

You should see:
```
✅ Email configuration test passed!
✅ Notification email sent successfully!
✅ Custom email sent successfully!
🎉 All email tests passed! Email service is ready for production.
```

---

## 🔒 **Security Notes**

- **App Passwords are safer** than using your main Gmail password
- **Each app password is unique** and can be revoked independently
- **2FA is required** for app passwords to work
- **Never share** your app password with others

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **"Username and Password not accepted"**
   - ✅ **Solution**: Use App Password instead of regular password
   - ✅ **Check**: 2FA is enabled on your Google account

2. **"App passwords not available"**
   - ✅ **Solution**: Enable 2-Factor Authentication first
   - ✅ **Check**: You're signed in to the correct Google account

3. **"Connection timeout"**
   - ✅ **Solution**: Check internet connection
   - ✅ **Check**: Firewall/antivirus isn't blocking SMTP

4. **"TLS/SSL errors"**
   - ✅ **Solution**: Ensure `EMAIL_USE_TLS=true` in .env
   - ✅ **Check**: SMTP port is 587 (not 465 or 25)

### **Verification Steps:**

1. **Check .env file**:
   ```env
   SYSTEM_EMAIL=keyegon@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USE_TLS=true
   ```

2. **Test configuration**:
   ```bash
   python test_email.py
   ```

3. **Check Gmail settings**:
   - 2FA enabled ✅
   - App password generated ✅
   - IMAP/POP enabled (optional) ✅

---

## 📞 **Support**

If you continue to have issues:

1. **Double-check** the app password was copied correctly
2. **Verify** 2FA is enabled on keyegon@gmail.com
3. **Try generating** a new app password
4. **Check** Google Account security settings

---

## 🎉 **Success Indicators**

When everything is working correctly, you'll receive:

1. **Test notification email** with FinSolve branding
2. **Custom HTML email** with system status
3. **Console confirmation** of successful sends

The emails will be sent from and to `keyegon@gmail.com` for testing purposes.

---

**Developed by Dr. Erick K. Yegon**  
**Email**: keyegon@gmail.com  
**Project**: FinSolve Technologies AI Assistant
