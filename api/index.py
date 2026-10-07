import os
from flask import Flask, jsonify, render_template_string
from supabase import create_client, Client

app = Flask(__name__)

HTML = r"""
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Supabase Health Check</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Inter,Arial,sans-serif;background:#f5f7fb;color:#172033}
.wrap{max-width:900px;margin:50px auto;padding:20px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:28px;box-shadow:0 12px 35px #0000000b}
h1{margin:0 0 8px;font-size:30px}.muted{color:#64748b;margin:0 0 25px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.item{border:1px solid #e5e7eb;border-radius:14px;padding:18px}.name{font-weight:700;margin-bottom:10px}.badge{display:inline-block;padding:6px 10px;border-radius:999px;font-size:13px;font-weight:700}
.ok{background:#dcfce7;color:#166534}.bad{background:#fee2e2;color:#991b1b}.warn{background:#fef3c7;color:#92400e}
.detail{font-size:13px;color:#64748b;margin-top:10px;word-break:break-word}
button{margin-top:22px;border:0;border-radius:10px;padding:12px 18px;background:#111827;color:#fff;cursor:pointer}
pre{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:12px;overflow:auto;margin-top:22px}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>Supabase Health Check</h1>
<p class="muted">Testing koneksi database dan layanan Supabase dari Vercel.</p>
<div id="grid" class="grid"></div>
<button onclick="run()">Test Lagi</button>
<pre id="raw">Menunggu...</pre>
</div>
</div>
<script>
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
function item(title,x){
 const cls=x.status==="ok"?"ok":x.status==="warn"?"warn":"bad";
 const label=x.status==="ok"?"TERHUBUNG":x.status==="warn"?"PERINGATAN":"GAGAL";
 return `<div class="item"><div class="name">${esc(title)}</div><span class="badge ${cls}">${label}</span><div class="detail">${esc(x.message)}</div></div>`;
}
async function run(){
 document.getElementById("grid").innerHTML=item("Supabase","{status:'warn',message:'Mengecek...'}");
 document.getElementById("raw").textContent="Loading...";
 try{
   const r=await fetch("/api/health",{cache:"no-store"});
   const d=await r.json();
   document.getElementById("grid").innerHTML=
     item("Environment",d.environment)+
     item("Database",d.database)+
     item("Auth",d.auth)+
     item("Storage",d.storage);
   document.getElementById("raw").textContent=JSON.stringify(d,null,2);
 }catch(e){
   document.getElementById("grid").innerHTML=item("API",{status:"error",message:e.message});
   document.getElementById("raw").textContent=e.stack||e.message;
 }
}
run();
</script>
</body>
</html>
"""

def result(status, message, **extra):
    return {"status": status, "message": message, **extra}

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/api/health")
def health():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    environment = result(
        "ok" if url and key else "error",
        "Environment variables tersedia." if url and key
        else "SUPABASE_URL dan/atau SUPABASE_SERVICE_ROLE_KEY belum diset."
    )

    if not url or not key:
        return jsonify({
            "ok": False,
            "environment": environment,
            "database": result("error", "Tidak dapat dites karena credentials belum tersedia."),
            "auth": result("error", "Tidak dapat dites karena credentials belum tersedia."),
            "storage": result("error", "Tidak dapat dites karena credentials belum tersedia.")
        }), 500

    try:
        supabase: Client = create_client(url, key)

        # Database: benar-benar melakukan query ke tabel test.
        try:
            response = supabase.table("connection_test").select("id").limit(1).execute()
            database = result("ok", "Query PostgreSQL berhasil.", rows=len(response.data or []))
        except Exception as e:
            database = result("error", f"Query database gagal: {str(e)}")

        # Auth: memanggil endpoint Auth menggunakan client Supabase.
        try:
            auth_response = supabase.auth.get_session()
            auth = result("ok", "Supabase Auth dapat diakses.")
        except Exception as e:
            auth = result("error", f"Auth gagal diakses: {str(e)}")

        # Storage: daftar bucket.
        try:
            buckets = supabase.storage.list_buckets()
            storage = result("ok", "Supabase Storage dapat diakses.", buckets=len(buckets or []))
        except Exception as e:
            storage = result("error", f"Storage gagal diakses: {str(e)}")

        all_ok = all(x["status"] == "ok" for x in [environment, database, auth, storage])

        return jsonify({
            "ok": all_ok,
            "environment": environment,
            "database": database,
            "auth": auth,
            "storage": storage
        }), 200 if all_ok else 207

    except Exception as e:
        return jsonify({
            "ok": False,
            "environment": environment,
            "database": result("error", "Client Supabase gagal dibuat."),
            "auth": result("error", "Tidak dapat dites."),
            "storage": result("error", "Tidak dapat dites."),
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
