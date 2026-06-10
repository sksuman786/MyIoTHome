# 🎯 cPanel Setup - START HERE (Super Simple)

## ⏱️ Time: 30 minutes total

---

## 📍 Step 1: Buy cPanel Hosting (5 minutes)

Pick ANY of these:
- **Bluehost** ($2.95/month) ← Good for beginners
- **HostGator** ($2.75/month)
- **SiteGround** ($3/month)
- **Namecheap** ($5/month)
- Or any host with cPanel

**What to look for:**
- ✅ cPanel included
- ✅ Python 3.8+ 
- ✅ MySQL/MariaDB
- ✅ SSH access

---

## 🗂️ Step 2: Login to cPanel (2 minutes)

After you buy hosting, you'll get an email with:
```
cPanel URL: something like cpanel.yourhost.com:2083
Username: your_username
Password: your_password
```

1. Open the cPanel URL in browser
2. Enter username & password
3. Click "Log In"

**You're now in cPanel!** ✅

---

## 📊 Step 3: Create Database (3 minutes)

In cPanel, find and click: **MySQL Databases**

1. Create database:
   - Name: `myhome_db`
   - Click "Create Database"

2. Create user:
   - Username: `myhome_user`
   - Password: `anything_long_and_random`
   - Click "Create User"

3. Add user to database:
   - Select `myhome_user` and `myhome_db`
   - Click "Add"
   - Check all boxes
   - Click "Make Changes"

**Save these for later:**
```
Database: myhome_db
Username: myhome_user
Password: what_you_entered
Host: localhost
```

---

## 📤 Step 4: Upload Your Project (5 minutes)

### Option A: Using cPanel File Manager (Easiest)

1. In cPanel, click: **File Manager**
2. Click "public_html" (main domain) OR create subdomain folder
3. Click "Upload" button
4. Drag & drop your `myhome` folder here
5. Wait for upload ✅

### Option B: Using FileZilla (Alternative)

1. Download FileZilla: https://filezilla-project.org
2. Open FileZilla
3. Go: File > Site Manager
4. Add new site:
   - Host: your-server.com
   - Protocol: SFTP
   - Username: cpanel_username
   - Password: cpanel_password
5. Click Connect
6. Drag `myhome` folder into right panel
7. Wait for upload ✅

---

## 🔌 Step 5: Connect via SSH (1 minute)

In cPanel, find: **Terminal** (or SSH)

Click it to open a black terminal window.

You're now in SSH! ✅

---

## 🐍 Step 6: Install Python Packages (5 minutes)

**In the SSH terminal, type:**

```bash
cd /path/to/myhome
```

(Replace with actual path - usually `/home/username/public_html/myhome`)

Then:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**This installs Django and everything else.**

Wait for it to finish... ✅

---

## ⚙️ Step 7: Configure Settings (3 minutes)

In cPanel File Manager:
1. Open `myhome/` folder
2. Right-click on `.env.example`
3. Click "Rename"
4. Change to `.env`
5. Double-click to edit it

**Edit these lines only:**

```
# Find this line and change:
DEBUG=False

# Find database section and change to:
DB_ENGINE=django.db.backends.mysql
DB_NAME=myhome_db
DB_USER=myhome_user
DB_PASSWORD=password_you_created_earlier
DB_HOST=localhost

# Change this to your domain:
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Leave rest as-is
```

Click "Save" ✅

---

## 🗄️ Step 8: Create Database Tables (2 minutes)

**Back in SSH terminal:**

```bash
python manage.py migrate
```

This creates all tables. ✅

---

## 👤 Step 9: Create Admin User (1 minute)

**In SSH terminal:**

```bash
python manage.py createsuperuser
```

Follow prompts:
```
Username: admin
Email: your@email.com
Password: strong_password_here
Password again: same_password
```

Save these! You'll need them to login. ✅

---

## 🎨 Step 10: Setup Web Server (3 minutes)

**Back in cPanel:**

1. Find: **Setup Python App** (or "Passenger")
2. Click "Create Application"
3. Fill in:
   - Python version: 3.8+ (pick highest)
   - Application root: `/home/username/public_html/myhome`
   - Application URL: `yourdomain.com` (or your subdomain)
   - Passenger log file: `logs/passenger.log`
   - Startup file: `myhome/wsgi.py`
4. Click "Create Application" ✅

---

## 🔒 Step 11: Enable HTTPS (2 minutes)

**In cPanel:**

1. Find: **SSL/TLS** or **AutoSSL**
2. Click to enable free SSL
3. Wait 5-10 minutes
4. Your site is now HTTPS ✅

---

## ✅ Step 12: Test Your Site (1 minute)

**Open browser and visit:**
```
https://yourdomain.com/admin/
```

You should see a login page!

**Login with credentials from Step 9**

You're now IN your admin panel! ✅

---

## 🎯 You're Done!

**Your site is now LIVE:**
- Admin: `https://yourdomain.com/admin/`
- Dashboard: `https://yourdomain.com/dashboard/`

---

## 🎮 What's Next?

### Option 1: Keep Exploring
1. Add a device in admin
2. Get the API key
3. Test creating appliances

### Option 2: Read More Docs
- **CPANEL_SETUP.md** - More detailed version
- **README.md** - Project overview
- **API_DOCUMENTATION.md** - For device integration

### Option 3: Setup Device Code
- Read **README.md** for Arduino/ESP8266 code
- Configure your device to connect to your server
- Control from dashboard!

---

## ⚠️ Common Issues

### "Can't find Terminal in cPanel"
→ Ask your host for SSH access or use File Manager approach

### "Python not installed"
→ Ask your host to enable Python 3.8+

### "Database error after login"
→ Check Database, Username, Password in `.env` match what you created

### "Static files not loading"
→ Run: `python manage.py collectstatic --noinput`

### "Page shows 500 error"
→ Check cPanel error logs in public_html/error_log

---

## 💡 Remember

- **Don't touch Docker** - it's for different people
- **cPanel is easier** - most hosting uses it
- **This works exactly** - same as Docker would
- **You got this!** 🚀

---

## 🎊 You Made It!

Your IoT home automation platform is now live on the internet!

Next: Enjoy controlling your smart home! 🏠💡

---

**Questions?** Check **CPANEL_SETUP.md** for more detailed steps.

**Ready to add devices?** Read **README.md** or **API_DOCUMENTATION.md**
