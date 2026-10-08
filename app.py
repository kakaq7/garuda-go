import os
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL dan SUPABASE_KEY wajib diatur di environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/")
def index():
    result = (
        supabase.table("items")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    items = result.data or []
    return render_template("index.html", items=items)


@app.route("/create", methods=["POST"])
def create():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Nama wajib diisi.", "error")
        return redirect(url_for("index"))

    supabase.table("items").insert({
        "name": name,
        "description": description
    }).execute()

    flash("Data berhasil ditambahkan.", "success")
    return redirect(url_for("index"))


@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit(item_id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Nama wajib diisi.", "error")
            return redirect(url_for("edit", item_id=item_id))

        supabase.table("items").update({
            "name": name,
            "description": description
        }).eq("id", item_id).execute()

        flash("Data berhasil diperbarui.", "success")
        return redirect(url_for("index"))

    result = (
        supabase.table("items")
        .select("*")
        .eq("id", item_id)
        .single()
        .execute()
    )

    if not result.data:
        flash("Data tidak ditemukan.", "error")
        return redirect(url_for("index"))

    return render_template("edit.html", item=result.data)


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    supabase.table("items").delete().eq("id", item_id).execute()
    flash("Data berhasil dihapus.", "success")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
