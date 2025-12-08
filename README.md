
# **Shortify – URL Shortener**

A URL shortening service built with **Django** and **Django REST Framework**, featuring analytics, QR codes, authentication and REST API.

---

## **Features**

### **Core Functionality**

* **URL Shortening** – Generate short, shareable links
* **Analytics Tracking** – Monitor clicks, referrers, devices, OS, and browsers
* **QR Code Generation** – Auto-generated QR codes for every short link
* **Expiration Control** – Optional expiration timestamps for links
* **User Accounts** – Register, log in, and manage your own URLs
* **REST API** – API with Swagger documentation

---

## ⚡ **Quick Start**

### **1. Clone the Repository**

```bash
git clone https://github.com/DawitMebrahtuG/shortify-django/
cd <directory_name>
```

### **2. Create a Virtual Environment**

```bash
python -m venv .shortenv
source .shortenv/bin/activate      # Windows: .shortenv\Scripts\activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Setup Environment**

```bash
cp .env.example .env
```

### **5. Apply Migrations**

```bash
python manage.py migrate
```

### **6. Create Superuser (Optional)**

```bash
python manage.py createsuperuser
```

### **7. Run the Development Server**

```bash
python manage.py runserver
```

Visit: **[http://localhost:8000](http://localhost:8000)**

---

## 📘 **API Documentation**

| Tool               | URL            |
| ------------------ | -------------- |
| **Swagger UI**     | `/api/docs/`   |
| **ReDoc**          | `/api/redoc/`  |
| **OpenAPI Schema** | `/api/schema/` |

---

## 🛠️ **Tech Stack**

* **Backend:** Django 5.2+
* **API Framework:** Django REST Framework 3.15+
* **Database:** SQLite (dev), PostgreSQL (prod)
* **API Docs:** drf-spectacular (OpenAPI 3.0)
* **QR Codes:** qrcode + Pillow
* **Analytics:** user-agents library

---

## 🔧 **Environment Variables**

Create a `.env` file in the project root:

```
DJANGO_SETTINGS_MODULE=shortener.settings.dev
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```
