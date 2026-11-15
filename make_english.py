# Run this inside the avishkar-solutions folder:  python make_english.py
import pathlib

R = [
 # app.py
 ("Final year ani MCA projects (Flask, web apps). Idea pasun coding ani deployment paryant guidance.",
  "Final-year and MCA projects (Flask, web apps). Guidance from idea to coding to deployment."),
 ("Clean, ATS-friendly resume ani LinkedIn profile. Fresher sathi khas.",
  "A clean, ATS-friendly resume and LinkedIn profile, built for freshers."),
 ("Interview prep ani job search strategy, IT ani Banking/Finance donhi sathi.",
  "Interview preparation and job search strategy for IT and Banking/Finance roles."),
 ("Stock, billing, purchase ani sales, medical distributors sathi complete management system.",
  "A complete management system for medical distributors: stock, billing, purchase and sales."),
 ("Naav ani phone kinva email dya, mhanje mi parat contact karu shakto.",
  "Please enter your name and a phone number or email so I can get back to you."),
 ("Message pohochla. Mi lavkarach contact karto.",
  "Message received. I will get back to you soon."),
 # base.html
 ("Final year projects, resume ani fresher career guidance, ek jaagi.",
  "Final-year projects, resume help and fresher career guidance, all in one place."),
 # home.html
 ("Idea pasun deployment paryant, tumcha project ani career.",
  "From idea to deployment: your project and your career."),
 ("Topic ani scope nakki", "Topic and scope finalised"),
 ("Project kinva resume sathi madat hava?", "Need help with your project or resume?"),
 # about.html
 ("Mi Avishkar, MCA student ani full stack developer. Mi Wolfox Pvt. Ltd., Kolhapur madhe Full Stack Developer intern mhanun kam kelay (Feb-May 2026).",
  "I am Avishkar, an MCA student and full stack developer. I completed a Full Stack Developer internship at Wolfox Pvt. Ltd., Kolhapur (February to May 2026)."),
 ("Mi swatah fresher mhanun jo process pahila, tyatun students la practical guidance deto: project, resume ani job search.",
  "I have been through the fresher journey myself, so I give students practical guidance on projects, resumes and job search."),
 # contact.html
 ("<label>Naav <input", "<label>Name <input"),
 ("<label>Kay hava?", "<label>What do you need?"),
 ("Kinva direct:", "Or reach me directly:"),
]

files = [pathlib.Path("app.py")] + sorted(pathlib.Path("templates").glob("*.html"))
for f in files:
    s = f.read_text(encoding="utf-8")
    o = s
    for a, b in R:
        s = s.replace(a, b)
    if s != o:
        f.write_text(s, encoding="utf-8")
        print("updated", f)

words = ["ani ", "kinva", "sathi", "pasun", "hava", "jaagi", "nakki", "madhe", "mhanun", "paryant", "tumcha", "dya", "karto", "Naav"]
left = []
for f in files:
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("#"):
            continue
        if any(w in line for w in words):
            left.append((f.name, i, line.strip()))
print("\nStill mixed-language lines:" if left else "\nAll visible text is English now.")
for x in left:
    print(x)
