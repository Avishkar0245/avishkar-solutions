# 🚀 Avishkar Solutions | Practical Tech & Career Mentorship

A modern, production-grade web application and Content Management System (CMS) built for **Avishkar Solutions** — an initiative dedicated to mentoring MCA and computer science students through final-year projects, ATS-optimized resumes, and viva preparation.

---

## 🌟 Key Highlights & Features

- **Dynamic CMS (Content Management System):** 
  - Add, manage, and delete portfolio projects directly from the Admin Dashboard without touching code.
  - Live updates for Founder profile, skills, and bio.
  - Manage real student testimonials and star ratings.
- **1-Click WhatsApp Connect:** Instant client/student outreach directly from the Admin Dashboard table with pre-filled enquiry templates.
- **Lead Capture & Enquiries Pipeline:** Contact forms seamlessly persist inquiries to **MongoDB Atlas** with status tracking (`New`, `Pending`, `Completed`).
- **Modern Responsive UI/UX:** Clean, responsive design featuring custom cards, glassmorphic header, floating WhatsApp action, and stats metrics.
- **Cloud-Ready Architecture:** Configured for seamless deployment with Gunicorn and Render.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **Database:** MongoDB Atlas (Cloud NoSQL via PyMongo)
- **Frontend:** HTML5, Modern CSS3, JavaScript, Font Awesome 6
- **Security:** Werkzeug password hashing, HMAC authentication, Environment-based secrets

---

## 📂 Project Structure

```text
avishkar-solutions/
│
├── app.py                   # Main Flask application & Admin CMS routes
├── requirements.txt         # Production dependencies
├── Procfile                 # Cloud web process entrypoint (Gunicorn)
├── .env.example             # Template for environment variables
├── static/
│   ├── css/
│   │   ├── style.css        # Modern, responsive styling
│   │   └── chat.css         # Chatbot styles
│   ├── js/
│   │   └── chat.js          # Chatbot logic
│   └── images/              # Assets & logos
└── templates/
    ├── base.html            # Master layout with FontAwesome & WhatsApp float
    ├── home.html            # Landing page with stats, roadmap & testimonials
    ├── about.html           # Dynamic founder story & core technologies
    ├── services.html        # Mentorship offerings & package breakdowns
    ├── portfolio.html       # Showcase of live projects & GitHub links
    ├── contact.html         # 2-column contact & inquiry capture form
    └── admin_dashboard.html # Full CMS dashboard for leads, projects & reviews
```

---

## ⚙️ Local Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/avishkar-solutions.git
   cd avishkar-solutions
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key_here
   MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD_HASH=your_scrypt_or_pbkdf2_hash
   ```

5. **Run the Application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

---

## 👨‍💻 Founder & Mentor

**Avishkar**  
*MCA Student | Full-Stack Developer | Project & Career Mentor*  
- **Location:** Karad, Maharashtra, India  
- **Internship:** Full Stack Developer Intern at Wolfox Pvt. Ltd. (Kolhapur)  
- **Specialization:** Python, Flask, MongoDB, Web Development & Career Guidance  

---

## 📄 License
This project is proprietary and maintained by Avishkar Solutions. All rights reserved.
