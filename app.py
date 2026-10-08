import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-in-production")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL, SUPABASE_KEY, dan SUPABASE_SERVICE_ROLE_KEY wajib diatur.")

supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def current_user():
    token = session.get("access_token")
    if not token:
        return None
    try:
        return supabase_auth.auth.get_user(token).user
    except Exception:
        session.clear()
        return None

def current_profile():
    user = current_user()
    if not user: return None
    return (supabase_admin.table("profiles").select("*").eq("id", str(user.id)).maybe_single().execute()).data

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user, profile = current_user(), current_profile()
        if not user:
            return redirect(url_for("login"))
        if not profile or profile.get("role") != "admin":
            flash("Akses admin diperlukan.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_auth():
    user = current_user()
    return {"current_user": user, "current_profile": current_profile() if user else None}

@app.route("/")
def index():
    if not current_user(): return render_template("landing.html")
    items = (supabase_admin.table("items").select("*").eq("status","approved").order("created_at", desc=True).execute()).data or []
    return render_template("index.html", items=items)

@app.route("/register", methods=["GET","POST"])
def register():
    if current_user(): return redirect(url_for("index"))
    if request.method == "POST":
        email, password = request.form.get("email","").strip().lower(), request.form.get("password","")
        if not email or not password or len(password) < 6:
            flash("Email wajib diisi dan password minimal 6 karakter.", "error")
            return render_template("register.html")
        try:
            r = supabase_auth.auth.sign_up({"email": email, "password": password})
            if r.session:
                session["access_token"], session["refresh_token"] = r.session.access_token, r.session.refresh_token
                flash("Registrasi berhasil.", "success")
                return redirect(url_for("index"))
            flash("Registrasi berhasil. Cek email untuk konfirmasi akun.", "success")
            return redirect(url_for("login"))
        except Exception as e: flash(f"Registrasi gagal: {e}", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if current_user(): return redirect(url_for("index"))
    if request.method == "POST":
        try:
            r = supabase_auth.auth.sign_in_with_password({"email":request.form.get("email","").strip().lower(),"password":request.form.get("password","")})
            session["access_token"], session["refresh_token"] = r.session.access_token, r.session.refresh_token
            flash("Login berhasil.", "success")
            return redirect(url_for("index"))
        except Exception as e: flash(f"Login gagal. Periksa email dan password. ({e})", "error")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/create", methods=["GET","POST"])
@login_required
def create():
    user = current_user()
    if request.method == "POST":
        name, description = request.form.get("name","").strip(), request.form.get("description","").strip()
        if not name:
            flash("Nama wajib diisi.", "error")
            return render_template("create.html")
        supabase_admin.table("items").insert({"name":name,"description":description,"created_by":str(user.id),"status":"pending"}).execute()
        flash("Data disimpan dan menunggu persetujuan admin.", "success")
        return redirect(url_for("index"))
    return render_template("create.html")

@app.route("/edit/<int:item_id>", methods=["GET","POST"])
@login_required
def edit(item_id):
    user, profile = current_user(), current_profile()
    item = (supabase_admin.table("items").select("*").eq("id",item_id).maybe_single().execute()).data
    if not item:
        flash("Data tidak ditemukan.", "error"); return redirect(url_for("index"))
    is_admin = profile and profile.get("role") == "admin"
    if not is_admin and item["created_by"] != str(user.id):
        flash("Anda tidak memiliki akses.", "error"); return redirect(url_for("index"))
    if request.method == "POST":
        payload = {"name":request.form.get("name","").strip(),"description":request.form.get("description","").strip()}
        if not payload["name"]:
            flash("Nama wajib diisi.", "error"); return render_template("edit.html", item=item)
        if not is_admin: payload.update(status="pending", approved_by=None, approved_at=None)
        supabase_admin.table("items").update(payload).eq("id",item_id).execute()
        flash("Data diperbarui. Jika diubah user, data kembali menunggu approval.", "success")
        return redirect(url_for("index"))
    return render_template("edit.html", item=item)

@app.post("/delete/<int:item_id>")
@login_required
def delete(item_id):
    user, profile = current_user(), current_profile()
    item = (supabase_admin.table("items").select("id,created_by").eq("id",item_id).maybe_single().execute()).data
    if not item:
        flash("Data tidak ditemukan.", "error"); return redirect(url_for("index"))
    if profile.get("role") != "admin" and item["created_by"] != str(user.id):
        flash("Anda tidak memiliki akses.", "error"); return redirect(url_for("index"))
    supabase_admin.table("items").delete().eq("id",item_id).execute()
    flash("Data dihapus.", "success")
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    items = (supabase_admin.table("items").select("*").order("created_at", desc=True).execute()).data or []
    return render_template("admin.html", items=items)

@app.post("/admin/items/<int:item_id>/approve")
@admin_required
def approve(item_id):
    user = current_user()
    supabase_admin.table("items").update({"status":"approved","approved_by":str(user.id)}).eq("id",item_id).execute()
    flash("Data disetujui.", "success"); return redirect(url_for("admin_dashboard"))

@app.post("/admin/items/<int:item_id>/reject")
@admin_required
def reject(item_id):
    supabase_admin.table("items").update({"status":"rejected","approved_by":None,"approved_at":None}).eq("id",item_id).execute()
    flash("Data ditolak.", "success"); return redirect(url_for("admin_dashboard"))

@app.get("/health")
def health(): return {"status":"ok"}

if __name__ == "__main__": app.run(debug=True)
