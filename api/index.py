import os
from flask import Flask, render_template, request, redirect
from supabase import create_client

app = Flask(__name__, template_folder="../templates")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL dan SUPABASE_KEY belum dikonfigurasi.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        email = request.form.get("email", "").strip()

        if nama and email:
            supabase.table("users").insert({
                "nama": nama,
                "email": email
            }).execute()

        return redirect("/")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
