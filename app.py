import os, json, datetime
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from functools import wraps
import hmac
from pymongo import MongoClient
import certifi



load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-fallback-secret-key-12345")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ---- SITE INFO ----
SITE = {
    "name": "Avishkar Solutions",
    "whatsapp": "91-9373510245",  # <-- येथे तुमचा खरा 10 आकडी नंबर टाका
    "email": "avishkarsolutions19@gmai.com",
    "linkedin": "https://linkedin.com",
    "github": "https://github.com",
}

# डिफॉल्ट सर्व्हिसेस
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

# डिफॉल्ट प्रोजेक्ट्स (बॅकअप)
PROJECTS = [
    {"title": "Medical Distribution Management System",
     "text": "A Complete Management System for Medical Distributors, Covering Inventory Management, Billing, Purchases, and Sales.",
     "tags": ["Flask", "Python", "MySQL"], "github": "#", "demo": ""},
    {"title": "GroceryMart",
     "text": "Full-stack grocery web app.",
     "tags": ["HTML", "CSS", "JavaScript", "Bootstrap", "Python", "MySQL"], "github": "#", "demo": ""},
]

# डिफॉल्ट About माहिती (बॅकअप)
DEFAULT_ABOUT = {
    "headline": "Hi, I'm Avishkar.",
    "intro": "MCA student, Full-Stack Developer, and Mentor helping freshers bridge the gap between college theory and industry-standard projects.",
    "experience": "I completed my Full Stack Developer Internship at Wolfox Pvt. Ltd., Kolhapur (Feb – May 2026), where I developed production-grade web systems and practical database architectures.",
    "vision": "Having navigated the fresher journey myself, I understand the challenges students face during final year viva, project submissions, and early job interviews. My goal with Avishkar Solutions is to provide honest, practical, 1-on-1 guidance without unnecessary fluff.",
    "skills": "Python, Flask, MongoDB Atlas, MySQL, JavaScript, HTML5, CSS3, Git, REST APIs"
}

# डिफॉल्ट विद्यार्थ्यांचे रिव्ह्यू (बॅकअप)
DEFAULT_REVIEWS = [
    {
        "name": "Prathamesh Kulkarni",
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


import urllib.parse

# WhatsApp नंबर क्लीन करणारा आणि URL एनकोड करणारा फिल्टर
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
            projs = list(_db.projects.find().sort("_id", -1))
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


# ---- ADMIN AUTH DECORATOR (हा आधी असणे गरजेचे आहे) ----
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


# ---- USER ROUTES ----
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
    db_error = None

    if _db is not None:
        try:
            total_enquiries = _db.leads.count_documents({})
            new_enquiries = _db.leads.count_documents({
                "$or": [{"status": "New"}, {"status": {"$exists": False}}, {"status": ""}]
            })
            enquiries = list(_db.leads.find().sort("created_at", -1).limit(50))
        except Exception as e:
            db_error = str(e)
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
        about=about_data,
        reviews=get_all_reviews(),
        db_error=db_error
    )

# नवीन रिव्ह्यू ॲड करणे
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

# रिव्ह्यू डिलीट करणे
@app.route("/admin/review/delete/<review_id>", methods=["POST"])
@admin_required
def admin_delete_review(review_id):
    if _db is None or not ObjectId.is_valid(review_id):
        flash("Invalid request or MongoDB not connected.", "error")
        return redirect(url_for("admin_dashboard"))

    _db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Review deleted successfully.", "ok")
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
        # विद्यार्थ्याचा डेटा मिळवणे
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

        # हा डेटा MongoDB मध्ये लीड म्हणून सेव्ह करा
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

        # रिझ्युमे प्रिव्ह्यू पेज दाखवा
        return render_template("resume_preview.html", r=resume_data)

    return render_template("resume_builder.html")

# ---- CHATBOT BLUEPRINT ----
try:
    from chatbot import chat_bp
    app.config["BOT_DATA"] = {"site": SITE, "services": SERVICES, "projects": PROJECTS}
    app.register_blueprint(chat_bp)
except Exception:
    pass

if __name__ == "__main__":
    app.run(debug=True)