
---

### 📄 `README.md`

# 📝 Notes App (Django)

A powerful yet simple notes application built with Django. Users can securely log in, add notes, search/filter them, and perform full CRUD operations on their notes. Clean design, intuitive flow, and robust backend!

---

## 🚀 Features

- 🔐 **User Authentication & Authorization**  
  - Sign up, log in, and log out securely  
  - Users can only manage their own notes  

- 🏠 **Home Page**  
  - Clean and welcoming landing page with intro and quick links  

- ➕ **Add Note**  
  - Create new notes with title and description  

- 📋 **View Notes**  
  - See all your notes in a styled list  
  - Filter by category and search by title  

- 🔍 **Search & Filter**  
  - Live search by note title  
  - Filter notes by predefined categories  

- 🛠️ **Edit & Delete**  
  - Edit existing notes  
  - Delete notes with safety measures  

- 📄 **Note Detail View**  
  - View full content of a single note  

- 🚫 **HTTP Method Protection**  
  - Disallows unsupported HTTP methods (e.g., POST on GET-only routes)  

---

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS (custom styled with dark-blue theme)
- **Database**: SQLite (default Django database)

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/Ouckland/note-taker.git
   cd notes-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. Open your browser and go to `http://127.0.0.1:8000/`

---

## 📂 Folder Structure (simplified)

```
notes_app/
│
├── notes/             # Notes app (models, views, urls, forms)
├── users/             # Custom user auth (signup/login/logout)
├── templates/         # All HTML templates
│   ├── partials/      # Shared components like header
│   └── ...
├── static/            # Static files (CSS, JS if any)
├── db.sqlite3         # SQLite DB
├── manage.py
└── README.md
```

---

## 💡 Future Improvements

- Tag support
- Rich-text editor for notes
- Dark/light mode toggle
- REST API support

---

## 🧑‍💻 Author

- Your Name — [Ouckland](https://github.com/Ouckland)

---

## 📄 License

This project is licensed under the MIT License. Feel free to use and customize it!
```

---

Let me know if you want it tailored with your GitHub link, project name, or screenshots section set up!