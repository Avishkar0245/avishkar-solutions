import os, json, datetime, urllib.parse, hmac
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from pymongo import MongoClient
import certifi
import requests

# Safe requests import (पायथनच्या बिल्ट-इन लायब्ररीसह)
try:
    import requests
except ImportError:
    requests = None
import urllib.request

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-fallback-secret-key-12345")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ---- SITE INFO ----
SITE = {
    "name": "Avishkar Solutions",
    "whatsapp": "91-9373510245",
    "email": "avishkarsolutions19@gmail.com",
    "linkedin": "https://linkedin.com",
    "github": "https://github.com",
}

# Default services
SERVICES = [
    {"title": "Project Mentoring",
     "text": "Final-year and MCA projects (Flask, web apps). Guidance from idea to coding to deployment.",
     "price": "Contact for price"},
    {"title": "Resume & LinkedIn",
     "text": "A clean, ATS-friendly resume and LinkedIn profile, built for freshers.",
     "price": "Contact for price"},
    {"title": "Career Guidance",
     "text": "Interview preparation and job search strategy for IT and Banking/Finance roles.",
     "price": "Contact for price"},
]

# Default projects (backup)
PROJECTS = [
    {"title": "Medical Distribution Management System",
     "text": "A Complete Management System for Medical Distributors, Covering Inventory Management, Billing, Purchases, and Sales.",
     "tags": ["Flask", "Python", "MySQL"], "github": "#", "demo": "",
     "image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&auto=format&fit=crop&q=80"},
    {"title": "GroceryMart",
     "text": "Full-stack grocery web app.",
     "tags": ["HTML", "CSS", "JavaScript", "Bootstrap", "Python", "MySQL"], "github": "#", "demo": "",
     "image": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&auto=format&fit=crop&q=80"},
]

# Default About information (backup)
DEFAULT_ABOUT = {
    "headline": "Hi, I'm Avishkar.",
    "intro": "MCA student, Full-Stack Developer, and Mentor helping freshers bridge the gap between college theory and industry-standard projects.",
    "experience": "I completed my Full Stack Developer Internship at Wolfox Pvt. Ltd., Kolhapur (Feb – May 2026), where I developed production-grade web systems and practical database architectures.",
    "vision": "Having navigated the fresher journey myself, I understand the challenges students face during final year viva, project submissions, and early job interviews. My goal with Avishkar Solutions is to provide honest, practical, 1-on-1 guidance without unnecessary fluff.",
    "skills": "Python, Flask, MongoDB Atlas, MySQL, JavaScript, HTML5, CSS3, Git, REST APIs"
}

# Default Students Review (Backup)
DEFAULT_REVIEWS = [
    {
        "name": "Harshad Patil",
        "role": "MCA Final Year, Kolhapur",
        "project": "Flask Medical Store App",
        "rating": 5,
        "comment": "Avishkar guided me from database schema to cloud deployment. I scored an A+ in my final viva and external examiner praised the clean architecture!",
    },
    {
        "name": "Snehal Patil",
        "role": "BCA Graduate",
        "project": "ATS Resume & LinkedIn",
        "rating": 5,
        "comment": "The resume revamp helped me get 3 interview calls within 2 weeks. The 1-on-1 mock interview tips gave me real confidence.",
    },
    {
        "name": "Rohit Shinde",
        "role": "Computer Engineering",
        "project": "GroceryMart Full-Stack",
        "rating": 5,
        "comment": "Clean code structure, zero errors during viva, and proper documentation support. Best mentor for college students!",
    }
]

def get_all_reviews():
    if _db is not None:
        try:
            revs = list(_db.reviews.find().sort("_id", -1))
            if revs:
                return revs
        except Exception as e:
            print("Error fetching reviews:", e)
    return DEFAULT_REVIEWS


# WhatsApp number clean and URL encode filters
@app.template_filter('wa_phone')
def wa_phone_filter(phone):
    if not phone:
        return ""
    clean = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(clean) == 10:
        return "91" + clean
    return clean

@app.template_filter('urlencode')
def urlencode_filter(s):
    if s is None:
        return ""
    return urllib.parse.quote(str(s))

# ---- MONGODB ATLAS CONNECTION ----
_db = None
_mongo_client = None

try:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is missing from .env")

    _mongo_client = MongoClient(
        mongo_uri,
        tls=True,
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=15000
    )
    _mongo_client.admin.command("ping")
    _db = _mongo_client["avishkar_solutions"]
    print("MongoDB Atlas Connected Successfully!")
except Exception as e:
    print("MongoDB Connection Failed:", e)
    _db = None


# ---- HELPER FUNCTIONS ----
def get_all_projects():
    if _db is not None:
        try:
            projs = list(_db.projects.find({
                "$or": [
                    {"status": "Approved"},
                    {"status": {"$exists": False}}
                ]
            }).sort("_id", -1))
            if projs:
                return projs
        except Exception as e:
            print("Error fetching projects:", e)
    return PROJECTS

def get_about_info():
    if _db is not None:
        try:
            about = _db.about.find_one({"type": "profile"})
            if about:
                return about
        except Exception as e:
            print("Error fetching about info:", e)
    return DEFAULT_ABOUT

def save_lead(lead):
    try:
        if _db is None:
            raise ConnectionError("MongoDB is not connected")
        _db.leads.insert_one(lead)
        print("Enquiry saved in MongoDB!")
    except Exception as e:
        print("MongoDB Save Error:", e)
        with open("leads.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(lead, default=str, ensure_ascii=False) + "\n")
        print("Enquiry saved in local JSON file.")


# ---- ADMIN AUTH DECORATOR ----
def admin_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view_function(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_site():
    return {"site": SITE}


# ---- USER PUBLIC ROUTES ----
@app.route("/")
def home():
    projects = get_all_projects()
    reviews = get_all_reviews()
    return render_template("home.html", services=SERVICES, projects=projects[:2], reviews=reviews)

@app.route("/services")
def services():
    return render_template("services.html", services=SERVICES)

@app.route("/portfolio")
def portfolio():
    projects = get_all_projects()
    return render_template("portfolio.html", projects=projects)

@app.route("/about")
def about():
    about_data = get_about_info()
    return render_template("about.html", about=about_data)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        lead = {k: request.form.get(k, "").strip() for k in ("name", "phone", "email", "interest", "message")}
        if not lead["name"] or not (lead["phone"] or lead["email"]):
            flash("Please enter your name and a phone number or email.", "error")
            return render_template("contact.html", form=lead)
        lead["created_at"] = datetime.datetime.utcnow()
        save_lead(lead)
        flash("Message received. I will get back to you soon.", "ok")
        return redirect(url_for("contact"))
    return render_template("contact.html", form={})


# ---- ADMIN AUTHENTICATION ----
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        saved_username = os.getenv("ADMIN_USERNAME", "")
        saved_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

        if (
            saved_username
            and saved_hash
            and hmac.compare_digest(username, saved_username)
            and check_password_hash(saved_hash, password)
        ):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password!", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("You have been logged out.", "ok")
    return redirect(url_for("admin_login"))


# ---- ADMIN DASHBOARD ----
@app.route("/admin")
@admin_required
def admin_dashboard():
    total_enquiries = 0
    new_enquiries = 0
    enquiries = []
    pending_projects = []
    db_error = None

    if _db is not None:
        try:
            total_enquiries = _db.leads.count_documents({})
            new_enquiries = _db.leads.count_documents({
                "$or": [{"status": "New"}, {"status": {"$exists": False}}, {"status": ""}]
            })
            enquiries = list(_db.leads.find().sort("created_at", -1).limit(50))
            pending_projects = list(_db.projects.find({"status": "Pending"}).sort("_id", -1))
        except Exception as e:
            db_error = str(e)
            print("Admin Dashboard Error:", e)
    else:
        db_error = "MongoDB is disconnected. Showing backup data."

    if not enquiries and os.path.exists("leads.jsonl"):
        try:
            with open("leads.jsonl", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        enquiries.append(json.loads(line))
            enquiries.reverse()
            total_enquiries = len(enquiries)
            new_enquiries = len(enquiries)
        except Exception:
            pass

    projects = get_all_projects()
    about_data = get_about_info()

    return render_template(
        "admin_dashboard.html",
        total_enquiries=total_enquiries,
        new_enquiries=new_enquiries,
        total_projects=len(projects),
        enquiries=enquiries,
        projects=projects,
        pending_projects=pending_projects,
        about=about_data,
        reviews=get_all_reviews(),
        db_error=db_error
    )


# ---- ADMIN APPROVE & REJECT PROJECT ----
@app.route("/admin/project/approve/<project_id>", methods=["POST"])
@admin_required
def admin_approve_project(project_id):
    if _db is not None and ObjectId.is_valid(project_id):
        _db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "Approved"}}
        )
        flash("Project approved! It is now live on the website.", "ok")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/project/reject/<project_id>", methods=["POST"])
@admin_required
def admin_reject_project(project_id):
    if _db is not None and ObjectId.is_valid(project_id):
        _db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "Rejected"}}
        )
        flash("Project rejected.", "error")
    return redirect(url_for("admin_dashboard"))


# ---- CMS: ADD & DELETE PROJECT ----
@app.route("/admin/project/add", methods=["POST"])
@admin_required
def admin_add_project():
    if _db is None:
        flash("MongoDB is not connected!", "error")
        return redirect(url_for("admin_dashboard"))

    title = request.form.get("title", "").strip()
    text = request.form.get("text", "").strip()
    tags_raw = request.form.get("tags", "").strip()
    github = request.form.get("github", "#").strip()
    demo = request.form.get("demo", "").strip()
    image = request.form.get("image", "").strip()

    if not title or not text:
        flash("Project title and description are required!", "error")
        return redirect(url_for("admin_dashboard"))

    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    new_proj = {
        "title": title,
        "text": text,
        "tags": tags,
        "github": github,
        "demo": demo,
        "image": image,
        "created_at": datetime.datetime.utcnow()
    }

    _db.projects.insert_one(new_proj)
    flash("Project added successfully to website!", "ok")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/project/delete/<project_id>", methods=["POST"])
@admin_required
def admin_delete_project(project_id):
    if _db is None or not ObjectId.is_valid(project_id):
        flash("Invalid request or MongoDB not connected.", "error")
        return redirect(url_for("admin_dashboard"))

    _db.projects.delete_one({"_id": ObjectId(project_id)})
    flash("Project deleted successfully.", "ok")
    return redirect(url_for("admin_dashboard"))


# ---- CMS: REVIEWS ----
@app.route("/admin/review/add", methods=["POST"])
@admin_required
def admin_add_review():
    if _db is None:
        flash("MongoDB is not connected!", "error")
        return redirect(url_for("admin_dashboard"))

    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip()
    project = request.form.get("project", "").strip()
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()

    if not name or not comment:
        flash("Name and review comment are required!", "error")
        return redirect(url_for("admin_dashboard"))

    new_rev = {
        "name": name,
        "role": role,
        "project": project,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.datetime.utcnow()
    }

    _db.reviews.insert_one(new_rev)
    flash("Student review added successfully to website!", "ok")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/review/delete/<review_id>", methods=["POST"])
@admin_required
def admin_delete_review(review_id):
    if _db is None or not ObjectId.is_valid(review_id):
        flash("Invalid request or MongoDB not connected.", "error")
        return redirect(url_for("admin_dashboard"))

    _db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Review deleted successfully.", "ok")
    return redirect(url_for("admin_dashboard"))


# ---- CMS: UPDATE ABOUT ----
@app.route("/admin/about/update", methods=["POST"])
@admin_required
def admin_update_about():
    if _db is None:
        flash("MongoDB is not connected!", "error")
        return redirect(url_for("admin_dashboard"))

    about_payload = {
        "type": "profile",
        "headline": request.form.get("headline", "").strip(),
        "intro": request.form.get("intro", "").strip(),
        "experience": request.form.get("experience", "").strip(),
        "vision": request.form.get("vision", "").strip(),
        "skills": request.form.get("skills", "").strip(),
        "updated_at": datetime.datetime.utcnow()
    }

    _db.about.update_one({"type": "profile"}, {"$set": about_payload}, upsert=True)
    flash("About information updated successfully on website!", "ok")
    return redirect(url_for("admin_dashboard"))


# ---- ENQUIRY STATUS & DELETE ----
@app.route("/admin/enquiry/update/<enquiry_id>", methods=["POST"])
@admin_required
def update_enquiry(enquiry_id):
    if _db is None or not ObjectId.is_valid(enquiry_id):
        flash("Invalid enquiry or database connection.", "error")
        return redirect(url_for("admin_dashboard"))

    status = request.form.get("status", "")
    if status in ["New", "Pending", "Completed"]:
        _db.leads.update_one({"_id": ObjectId(enquiry_id)}, {"$set": {"status": status}})
        flash("Enquiry status updated.", "ok")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/enquiry/delete/<enquiry_id>", methods=["POST"])
@admin_required
def delete_enquiry(enquiry_id):
    if _db is None or not ObjectId.is_valid(enquiry_id):
        flash("Invalid enquiry or database connection.", "error")
        return redirect(url_for("admin_dashboard"))

    _db.leads.delete_one({"_id": ObjectId(enquiry_id)})
    flash("Enquiry deleted successfully.", "ok")
    return redirect(url_for("admin_dashboard"))


# ---- ATS RESUME BUILDER ROUTE ----
@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():
    if request.method == "POST":
        resume_data = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "linkedin": request.form.get("linkedin", "").strip(),
            "github": request.form.get("github", "").strip(),
            "location": request.form.get("location", "").strip(),
            "summary": request.form.get("summary", "").strip(),
            "education": request.form.get("education", "").strip(),
            "college": request.form.get("college", "").strip(),
            "year": request.form.get("year", "").strip(),
            "skills": request.form.get("skills", "").strip(),
            "project1_title": request.form.get("project1_title", "").strip(),
            "project1_desc": request.form.get("project1_desc", "").strip(),
            "project2_title": request.form.get("project2_title", "").strip(),
            "project2_desc": request.form.get("project2_desc", "").strip(),
            "experience": request.form.get("experience", "").strip(),
            "certifications": request.form.get("certifications", "").strip(),
        }

        if _db is not None and resume_data["name"] and resume_data["phone"]:
            lead = {
                "name": resume_data["name"],
                "phone": resume_data["phone"],
                "email": resume_data["email"],
                "interest": "ATS Resume Builder (Created Resume)",
                "message": f"College: {resume_data.get('college')} | Skills: {resume_data.get('skills')[:50]}",
                "created_at": datetime.datetime.utcnow(),
                "status": "New"
            }
            try:
                _db.leads.insert_one(lead)
            except Exception as e:
                print("Lead save error from resume builder:", e)

        return render_template("resume_preview.html", r=resume_data)

    return render_template("resume_builder.html")


# ==========================================
# USER (STUDENT) AUTHENTICATION & DASHBOARD
# ==========================================

def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to access your dashboard.", "error")
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return decorated_function


# 1. Student Register
@app.route("/register", methods=["GET", "POST"])
def user_register():
    if session.get("user_id"):
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        college = request.form.get("college", "").strip()
        github = request.form.get("github", "").strip()

        if not name or not email or not password:
            flash("Name, email and password are required!", "error")
            return render_template("user_register.html")

        if _db is not None:
            existing = _db.users.find_one({"email": email})
            if existing:
                flash("This email is already registered! Please login.", "error")
                return redirect(url_for("user_login"))

            user_doc = {
                "name": name,
                "email": email,
                "password_hash": generate_password_hash(password),
                "college": college,
                "github": github,
                "created_at": datetime.datetime.utcnow()
            }
            res = _db.users.insert_one(user_doc)
            
            session["user_id"] = str(res.inserted_id)
            session["user_name"] = name
            session["user_email"] = email
            flash(f"Welcome, {name}! Your account has been created.", "ok")
            return redirect(url_for("user_dashboard"))
        else:
            flash("Database offline. Please try again later.", "error")

    return render_template("user_register.html")


# 2. Student Login
@app.route("/login", methods=["GET", "POST"])
def user_login():
    if session.get("user_id"):
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if _db is not None:
            user = _db.users.find_one({"email": email})
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = str(user["_id"])
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                flash("Login successful! Welcome back.", "ok")
                return redirect(url_for("user_dashboard"))

        flash("Invalid email or password!", "error")

    return render_template("user_login.html")


# 3. Student Logout
@app.route("/logout")
def user_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    flash("You have been logged out successfully.", "ok")
    return redirect(url_for("home"))


# 4. Student Dashboard
@app.route("/user/dashboard")
@user_login_required
def user_dashboard():
    user_projects = []
    user_info = None

    if _db is not None:
        user_info = _db.users.find_one({"_id": ObjectId(session["user_id"])})
        user_projects = list(_db.projects.find({"user_id": session["user_id"]}).sort("_id", -1))

    return render_template("user_dashboard.html", user=user_info, projects=user_projects)


# 5. Student New Project Submit (Status: Pending)
@app.route("/user/project/submit", methods=["POST"])
@user_login_required
def user_submit_project():
    if _db is None:
        flash("Database is offline. Try again later.", "error")
        return redirect(url_for("user_dashboard"))

    title = request.form.get("title", "").strip()
    text = request.form.get("text", "").strip()
    tags_raw = request.form.get("tags", "").strip()
    github = request.form.get("github", "").strip()
    demo = request.form.get("demo", "").strip()
    image = request.form.get("image", "").strip()

    if not title or not text or not github:
        flash("Title, description, and your GitHub repository link are required!", "error")
        return redirect(url_for("user_dashboard"))

    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    user = _db.users.find_one({"_id": ObjectId(session["user_id"])})

    new_project = {
        "title": title,
        "text": text,
        "tags": tags,
        "github": github,
        "demo": demo,
        "image": image,
        "user_id": session["user_id"],
        "user_name": user.get("name", "Student Developer") if user else "Student Developer",
        "user_college": user.get("college", "College Student") if user else "College Student",
        "user_github": user.get("github", github) if user else github,
        "status": "Pending",
        "created_at": datetime.datetime.utcnow()
    }

    _db.projects.insert_one(new_project)
    flash("Project submitted successfully! It is now Pending for admin review. Once approved, it will be published on the live website.", "ok")
    return redirect(url_for("user_dashboard"))


# ==========================================
# AVISHKAR SOLUTIONS AI ASSISTANT (GEMINI AI)
# ==========================================
# ==========================================
# AVISHKAR SOLUTIONS AI ASSISTANT (GEMINI AI)
# ==========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    
    # थेट मेसेज आला असल्यास
    if not messages and data.get("message"):
        messages = [{"role": "user", "content": data.get("message")}]
        
    if not messages:
        return jsonify(reply="Please type a message."), 400

    latest_msg = messages[-1].get("content", "").strip() if isinstance(messages[-1], dict) else ""
    if not latest_msg:
        return jsonify(reply="Please type a question."), 400

    # जर Gemini API Key असेल तर उत्तर मिळवा
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            
            # मागील ५ संभाषणांचा संदर्भ (Context Memory)
            contents = []
            for m in messages[-6:]:
                role = "user" if m.get("role") == "user" else "model"
                text = m.get("content", "").strip()
                if text:
                    contents.append({"role": role, "parts": [{"text": text}]})
            
            payload = {
                "system_instruction": {
                    "parts": [{
                        "text": (
                            "You are the official AI Assistant for 'Avishkar Solutions', founded by Avishkar, an MCA student and full-stack developer (Python, Flask, JavaScript, MySQL, MongoDB). "
                            "Avishkar Solutions specializes in:\n"
                            "1) Final-Year & MCA Project Mentoring (Python, Flask, Web apps, Database systems, idea selection, live deployment, viva preparation).\n"
                            "2) Harvard-style ATS Resume Building and LinkedIn optimization for freshers.\n"
                            "3) IT and Banking/Finance Fresher Career Guidance.\n\n"
                            "Strict Guidelines:\n"
                            "- Never reveal the underlying AI model name (like Gemini, Google, OpenAI, Anthropic). Always introduce or act as 'Avishkar Solutions AI'.\n"
                            "- Answer in the exact same language the user asks (fluent Marathi, English, or Hindi).\n"
                            "- Keep answers friendly, crisp, and helpful (2 to 4 sentences). If a student asks for project ideas, suggest 2-3 trending, practical topics with tech stack.\n"
                            "- If they ask about fees, paid mentoring, or customized projects, warmly invite them to message Avishkar on WhatsApp at +91-9373510245 or visit the Contact page."
                        )
                    }]
                },
                "contents": contents if contents else [{"role": "user", "parts": [{"text": latest_msg}]}],
                "generationConfig": {
                    "maxOutputTokens": 350,
                    "temperature": 0.7
                }
            }
            
            # --- येथे हा कोड लागतो (requests किंवा urllib द्वारे कॉल) ---
            if requests is not None:
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    res_data = res.json()
                    reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return jsonify(reply=reply_text)
            else:
                # Built-in Python fallback (कोणत्याही एक्स्ट्रा पॅकेजशिवाय चालणारा)
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return jsonify(reply=reply_text)

        except Exception as e:
            app.logger.warning(f"AI API Error: {e}")

    # Fallback (BAckup Ans,  API are a busy)
    return jsonify(
        reply="नमस्कार! मी Avishkar Solutions चा AI असिस्टंट आहे. फायनल इयर प्रोजेक्ट, विवा प्रश्न किंवा रेझ्युमेबद्दल विचारा, किंवा WhatsApp वर थेट संपर्क करा!"
    )
 


if __name__ == "__main__":
    app.run(debug=True)