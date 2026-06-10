# 📂 What to Upload to cPanel - File Guide

## ✅ Upload These Folders/Files

```
myhome/                          ← Upload this ENTIRE folder
│
├── accounts/                    ✅ UPLOAD
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   └── ...
│
├── devices/                     ✅ UPLOAD
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   └── ...
│
├── api/                         ✅ UPLOAD
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── dashboard/                   ✅ UPLOAD
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── notifications/               ✅ UPLOAD
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── websocket/                   ✅ UPLOAD
│   ├── consumers.py
│   ├── routing.py
│   └── ...
│
├── templates/                   ✅ UPLOAD
│   ├── base.html
│   ├── accounts/
│   └── dashboard/
│
├── static/                      ✅ UPLOAD
│   ├── css/
│   └── js/
│
├── myhome/                      ✅ UPLOAD (Django config)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── __init__.py
│
├── manage.py                    ✅ UPLOAD
├── requirements.txt             ✅ UPLOAD
├── .env.example                 ✅ UPLOAD
│
├── logs/                        ✅ CREATE (empty folder on cPanel)
├── media/                       ✅ CREATE (empty folder on cPanel)
│
├── ❌ Dockerfile                DELETE (Docker only)
├── ❌ docker-compose.yml        DELETE (Docker only)
├── ❌ nginx.conf                DELETE (Docker only)
├── ❌ setup.sh                  DELETE (Docker only)
│
└── ✅ CPANEL_SETUP.md           (Read this!)
    ✅ NO_DOCKER_GUIDE.md        (Reference this!)
    ✅ README.md                 (Optional reading)
    ✅ API_DOCUMENTATION.md      (Reference this!)

```

---

## 📋 Files to KEEP vs DELETE

### ✅ KEEP These (Upload to cPanel)
```
myhome/          (entire project)
accounts/        (app)
devices/         (app)
api/             (app)
dashboard/       (app)
notifications/   (app)
websocket/       (app)
templates/       (HTML)
static/          (CSS, JS)
manage.py        (main script)
requirements.txt (packages list)
.env.example     (settings template)
```

### ❌ DELETE These (Docker stuff, you don't need)
```
Dockerfile           ✋ Don't upload
docker-compose.yml   ✋ Don't upload
nginx.conf          ✋ Don't upload
setup.sh            ✋ Don't upload
```

### 📚 Documentation (Optional)
```
README.md                    (nice to have)
API_DOCUMENTATION.md         (keep for reference)
CPANEL_SETUP.md             (MUST READ)
NO_DOCKER_GUIDE.md          (MUST READ)
QUICKSTART.md               (updated with cPanel option)
```

---

## 🔧 Step-by-Step Upload Guide

### Using FileZilla (Easy)

```
1. Download FileZilla: https://filezilla-project.org
2. Open FileZilla
3. Go: File > Site Manager
4. Add new site:
   - Name: My cPanel Host
   - Host: your-server.com
   - Protocol: SFTP
   - Port: 22
   - Username: cpanel_username
   - Password: cpanel_password
5. Click Connect
6. Navigate to public_html or your folder
7. Drag and drop the myhome/ folder
8. Wait for upload (might take 5 minutes)
```

### Using cPanel File Manager (Easier)

```
1. Login to cPanel
2. Click "File Manager"
3. Navigate to your upload location
4. Click "Upload" button
5. Select myhome/ folder (or zip it first)
6. Click Upload
7. Wait for completion
```

### Using SSH (Most Technical)

```bash
# From your computer (macOS/Linux Terminal)
scp -r myhome/ username@server.com:/path/to/upload/

# Or compress first
tar -czf myhome.tar.gz myhome/
scp myhome.tar.gz username@server.com:/path/to/upload/

# Then SSH and extract
ssh username@server.com
cd /path/to/upload/
tar -xzf myhome.tar.gz
```

---

## 📁 What Each Folder Does

| Folder | Purpose | Upload? |
|--------|---------|---------|
| `accounts/` | User login & auth | ✅ Yes |
| `devices/` | Device management | ✅ Yes |
| `api/` | REST APIs | ✅ Yes |
| `dashboard/` | Web dashboard | ✅ Yes |
| `notifications/` | Email alerts | ✅ Yes |
| `websocket/` | Real-time updates | ✅ Yes |
| `templates/` | HTML pages | ✅ Yes |
| `static/` | CSS & JavaScript | ✅ Yes |
| `myhome/` | Django config | ✅ Yes |
| `logs/` | App logs | ✅ Create empty |
| `media/` | User uploads | ✅ Create empty |
| `venv/` | Python packages | ❌ No (create on host) |

---

## ⚠️ Important Notes

### 1. Don't Upload venv/
```
❌ DON'T upload the venv/ folder
✅ Instead: Create new venv on cPanel host
```

Reason: venv is specific to your computer. Create a fresh one on cPanel.

### 2. Don't Upload __pycache__/
```
❌ DON'T upload __pycache__/ folders
✅ They'll be created automatically
```

### 3. Create Folders on cPanel
```
Create these EMPTY folders via cPanel after uploading:

logs/
media/

(These are for app use)
```

### 4. Rename .env.example
```
After uploading .env.example:

.env.example → .env

Then edit .env with your cPanel database settings
```

---

## ✅ Final Checklist Before Upload

- [ ] You have FileZilla or cPanel File Manager ready
- [ ] You have your cPanel FTP/SFTP credentials
- [ ] You know where to upload (ask your host)
- [ ] You have the myhome/ folder on your computer
- [ ] You removed Docker files (optional but clean)
- [ ] You have 100+ MB free space on cPanel
- [ ] You read CPANEL_SETUP.md

---

## 🚀 After Upload

```
1. Open CPANEL_SETUP.md
2. Follow Step 3: "Install Python Packages via SSH"
3. Continue with remaining steps
4. Your site will be live!
```

---

## 💡 Pro Tips

### Zip First for Faster Upload
```bash
# On your computer
zip -r myhome.zip myhome/

# Then upload .zip file to cPanel
# Extract it in cPanel File Manager
```

### Check Upload Progress
```bash
# In SSH after uploading
ls -la /path/to/myhome/
du -sh /path/to/myhome/

# Should show your files
```

### Fix Permissions (if needed)
```bash
# SSH commands
chmod 755 /path/to/myhome/
chmod 644 /path/to/myhome/*.py
```

---

## ❓ What If I'm Confused?

**Just follow this order:**
1. Read: **NO_DOCKER_GUIDE.md** ← Simple explanation
2. Read: **CPANEL_SETUP.md** ← Step by step
3. Upload files as shown above
4. Follow CPANEL_SETUP.md steps
5. Done!

**You don't need to understand everything.** Just follow the steps.

---

**Ready? Let's go! 🚀**

**Next Step**: Open **CPANEL_SETUP.md** and start at Step 1!
