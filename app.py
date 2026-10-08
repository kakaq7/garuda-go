import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL dan SUPABASE_KEY wajib diatur.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def admin_client():
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY wajib diatur untuk fitur admin.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def current_user():
    return session.get("user")

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Silakan login terlebih dahulu untuk melanjutkan.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.get("is_admin"):
            flash("Akses admin diperlukan.", "danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {"current_user": current_user()}

@app.route("/")
def index():
    # Only verified/published records are public.
    result = supabase.table("players").select(
        "id,full_name,slug,age_group,position,city,province,club_name,photo_url,short_bio"
    ).eq("status", "verified").order("created_at", desc=True).limit(12).execute()
    return render_template("index.html", players=result.data or [])

@app.route("/pemain")
def players():
    q = request.args.get("q", "").strip()
    province = request.args.get("province", "").strip()
    position = request.args.get("position", "").strip()
    age_group = request.args.get("age_group", "").strip()

    query = supabase.table("players").select(
        "id,full_name,slug,age_group,position,city,province,club_name,photo_url,short_bio"
    ).eq("status", "verified")

    if q:
        # ilike on full_name/city/club is handled with OR.
        safe = q.replace(",", "")
        query = query.or_(f"full_name.ilike.%{safe}%,city.ilike.%{safe}%,club_name.ilike.%{safe}%")
    if province:
        query = query.eq("province", province)
    if position:
        query = query.eq("position", position)
    if age_group:
        query = query.eq("age_group", age_group)

    result = query.order("full_name").limit(100).execute()
    return render_template(
        "players.html",
        players=result.data or [],
        filters={"q": q, "province": province, "position": position, "age_group": age_group},
    )

@app.route("/pemain/<slug>")
def player_detail(slug):
    result = supabase.table("players").select("*").eq("slug", slug).eq("status", "verified").limit(1).execute()
    player = (result.data or [None])[0]
    if not player:
        return render_template("404.html"), 404
    return render_template("player_detail.html", player=player)

@app.route("/tentang")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
            user_id = auth.user.id
            profile = supabase.table("profiles").select("display_name,is_admin").eq("id", user_id).limit(1).execute()
            p = (profile.data or [{}])[0]
            session["user"] = {
                "id": user_id,
                "email": auth.user.email,
                "display_name": p.get("display_name") or auth.user.email.split("@")[0],
                "is_admin": bool(p.get("is_admin")),
                "access_token": auth.session.access_token if auth.session else None,
            }
            flash("Login berhasil. Selamat datang kembali!", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        except Exception:
            flash("Email atau password tidak valid.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if len(name) < 2 or len(password) < 8:
            flash("Nama minimal 2 karakter dan password minimal 8 karakter.", "warning")
            return render_template("register.html")
        try:
            auth = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"display_name": name}}})
            if auth.user and not auth.session:
                flash("Registrasi berhasil. Silakan cek email untuk verifikasi akun.", "success")
            else:
                flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))
        except Exception as exc:
            flash(f"Registrasi gagal: {str(exc)}", "danger")
    return render_template("register.html")

@app.route("/logout")
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("index"))

@app.route("/kontribusi", methods=["GET", "POST"])
@login_required
def contribute():
    if request.method == "POST":
        data = {
            "full_name": request.form.get("full_name", "").strip(),
            "birth_year": request.form.get("birth_year") or None,
            "age_group": request.form.get("age_group", "").strip(),
            "position": request.form.get("position", "").strip(),
            "city": request.form.get("city", "").strip(),
            "province": request.form.get("province", "").strip(),
            "club_name": request.form.get("club_name", "").strip(),
            "photo_url": request.form.get("photo_url", "").strip() or None,
            "short_bio": request.form.get("short_bio", "").strip(),
            "source_url": request.form.get("source_url", "").strip() or None,
            "evidence_notes": request.form.get("evidence_notes", "").strip(),
            "submitted_by": current_user()["id"],
            "status": "pending",
        }
        if not data["full_name"] or not data["age_group"] or not data["position"] or not data["province"]:
            flash("Nama, kelompok usia, posisi, dan provinsi wajib diisi.", "warning")
            return render_template("contribute.html", form=data)
        try:
            supabase.table("players").insert(data).execute()
            flash("Kontribusi berhasil dikirim dan menunggu verifikasi admin.", "success")
            return redirect(url_for("my_contributions"))
        except Exception as exc:
            flash(f"Gagal mengirim kontribusi: {str(exc)}", "danger")
    return render_template("contribute.html", form={})

@app.route("/kontribusi-saya")
@login_required
def my_contributions():
    result = supabase.table("players").select(
        "id,full_name,age_group,position,province,club_name,status,rejection_reason,created_at"
    ).eq("submitted_by", current_user()["id"]).order("created_at", desc=True).execute()
    return render_template("my_contributions.html", players=result.data or [])

@app.route("/admin")
@admin_required
def admin_dashboard():
    client = admin_client()
    pending = client.table("players").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    counts = {}
    for status in ["pending", "verified", "rejected"]:
        r = client.table("players").select("id", count="exact").eq("status", status).execute()
        counts[status] = r.count or 0
    return render_template("admin.html", players=pending.data or [], counts=counts)

@app.route("/admin/pemain/<player_id>/verify", methods=["POST"])
@admin_required
def verify_player(player_id):
    client = admin_client()
    client.table("players").update({
        "status": "verified",
        "rejection_reason": None,
        "verified_by": current_user()["id"],
    }).eq("id", player_id).execute()
    flash("Data pemain berhasil diverifikasi.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/pemain/<player_id>/reject", methods=["POST"])
@admin_required
def reject_player(player_id):
    reason = request.form.get("reason", "").strip()
    client = admin_client()
    client.table("players").update({
        "status": "rejected",
        "rejection_reason": reason or "Data belum memenuhi kriteria verifikasi.",
        "verified_by": current_user()["id"],
    }).eq("id", player_id).execute()
    flash("Data ditolak dan dikembalikan ke pengusul.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "sipps-indonesia"})

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
