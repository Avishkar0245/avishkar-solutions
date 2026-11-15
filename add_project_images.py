# Run inside the avishkar-solutions folder:  python add_project_images.py
import pathlib

IMAGES = {
    "Medical Distribution Management System": "images/projects/medical-distribution.png",
    "GroceryMart": "images/projects/grocerymart.png",
    "GreenCart": "images/projects/greencart.png",
}
IMG_TAG = ('{% if p.image %}<img class="shot" src="{{ url_for(\'static\', filename=p.image) }}" '
           'alt="{{ p.title }} screenshot" loading="lazy" onerror="this.remove()">{% endif %}')
CSS = """
.shot{display:block;width:100%;max-width:560px;aspect-ratio:16/10;object-fit:cover;object-position:top;border:1px solid var(--line);border-radius:8px;margin:0 0 .9rem;background:#fff}
"""

if not pathlib.Path("app.py").exists():
    raise SystemExit("Run this inside the avishkar-solutions folder (where app.py is).")

pathlib.Path("static/images/projects").mkdir(parents=True, exist_ok=True)
print("folder ready: static/images/projects")

app = pathlib.Path("app.py"); s = app.read_text(encoding="utf-8"); o = s
for title, img in IMAGES.items():
    key = '{"title": "%s",' % title
    if key in s and ('"image": "%s"' % img) not in s:
        s = s.replace(key, key + '\n     "image": "%s",' % img, 1)
    elif key not in s:
        print("! project not found in app.py:", title)
if s != o:
    app.write_text(s, encoding="utf-8"); print("patched app.py")

for name in ("portfolio.html", "home.html"):
    p = pathlib.Path("templates") / name
    t = p.read_text(encoding="utf-8")
    old = '<div class="row"><h3>{{ p.title }}</h3>'
    if 'class="shot"' in t:
        continue
    if old in t:
        p.write_text(t.replace(old, '<div class="row project">' + IMG_TAG + '<h3>{{ p.title }}</h3>'), encoding="utf-8")
        print("patched templates/" + name)
    else:
        print("! project card not found in", name)

css = pathlib.Path("static/css/style.css"); c = css.read_text(encoding="utf-8")
if ".shot{" not in c:
    css.write_text(c.rstrip() + "\n" + CSS, encoding="utf-8"); print("patched static/css/style.css")

print("\nNow save your screenshots (PNG) in static/images/projects/ with these names:")
for img in IMAGES.values():
    print("  ", pathlib.Path(img).name)
print("Then restart: python app.py and press Ctrl + F5.")
