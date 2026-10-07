import os
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import check_password_hash

try:
    from supabase import create_client
except ImportError:
    create_client = None

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-only-change-this-secret-before-deploying')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(os.getenv('VERCEL'))

SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').strip()
_db = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        _db = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        _db = None

# Demonstration content is used only when Supabase is not configured/reachable.
DEMO_PLAYERS = [
    {'id':'demo-1','name':'Rizky Pratama','age':17,'birth_year':2009,'position':'Gelandang','club':'Akademi Garuda Muda','province':'Jawa Barat','stage':'U-18','summary':'Gelandang box-to-box dengan visi bermain dan distribusi bola yang baik.','status':'published','created_at':'2026-09-14T08:00:00+00:00','source_name':'Scout komunitas Bandung'},
    {'id':'demo-2','name':'Bagas Saputra','age':19,'birth_year':2007,'position':'Penyerang','club':'PS Kota Surakarta','province':'Jawa Tengah','stage':'U-20','summary':'Penyerang dengan pergerakan tanpa bola dan penyelesaian akhir menjanjikan.','status':'published','created_at':'2026-09-12T08:00:00+00:00','source_name':'Pelatih lokal'},
    {'id':'demo-3','name':'Made Aditya','age':15,'birth_year':2011,'position':'Bek tengah','club':'Bali Youth Football','province':'Bali','stage':'U-16','summary':'Bek tengah yang kuat dalam duel udara dan nyaman membangun serangan.','status':'published','created_at':'2026-09-10T08:00:00+00:00','source_name':'Orang tua pemain'},
    {'id':'demo-4','name':'Fajar Ramadhan','age':22,'birth_year':2004,'position':'Penjaga gawang','club':'Persikab Kabupaten Bandung','province':'Jawa Barat','stage':'Senior','summary':'Kiper dengan refleks cepat dan komunikasi yang aktif di lini belakang.','status':'published','created_at':'2026-09-08T08:00:00+00:00','source_name':'Pengamat sepak bola'},
    {'id':'demo-5','name':'Andi Kurniawan','age':13,'birth_year':2013,'position':'Sayap','club':'SSB Makassar United','province':'Sulawesi Selatan','stage':'U-14','summary':'Pemain sayap eksplosif, masih dalam tahap pengembangan teknik dasar.','status':'published','created_at':'2026-09-06T08:00:00+00:00','source_name':'Pelatih SSB'},
    {'id':'demo-6','name':'Dimas Putra','age':16,'birth_year':2010,'position':'Bek kanan','club':'Akademi Nusantara','province':'DI Yogyakarta','stage':'U-18','summary':'Memiliki stamina baik, disiplin bertahan, dan progres umpan silang.','status':'published','created_at':'2026-09-05T08:00:00+00:00','source_name':'Scout komunitas'},
]


def db_ready():
    return _db is not None


def fetch_players(status='published', limit=100):
    if db_ready():
        try:
            q = _db.table('players').select('*').eq('status', status).order('created_at', desc=True).limit(limit)
            return q.execute().data or []
        except Exception:
            app.logger.exception('Supabase fetch players failed')
    return [p.copy() for p in DEMO_PLAYERS if p['status'] == status][:limit]


def fetch_submissions(status=None, limit=200):
    if db_ready():
        try:
            q = _db.table('players').select('*').order('created_at', desc=True).limit(limit)
            if status:
                q = q.eq('status', status)
            return q.execute().data or []
        except Exception:
            app.logger.exception('Supabase fetch submissions failed')
    return [p.copy() for p in DEMO_PLAYERS if not status or p['status'] == status][:limit]


def insert_player(data):
    if db_ready():
        try:
            _db.table('players').insert(data).execute()
            return True
        except Exception:
            app.logger.exception('Supabase insert failed')
            return False
    # Demo mode acknowledges form flow but does not persist data between invocations.
    DEMO_PLAYERS.insert(0, {**data, 'id': 'demo-' + str(len(DEMO_PLAYERS)+1), 'created_at': datetime.now(timezone.utc).isoformat()})
    return True


def update_player_status(player_id, status, note=''):
    if db_ready():
        try:
            payload = {'status': status, 'review_note': note, 'reviewed_at': datetime.now(timezone.utc).isoformat()}
            _db.table('players').update(payload).eq('id', player_id).execute()
            return True
        except Exception:
            app.logger.exception('Supabase update failed')
            return False
    for player in DEMO_PLAYERS:
        if str(player['id']) == str(player_id):
            player['status'] = status
            player['review_note'] = note
            return True
    return False


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Silakan masuk sebagai admin terlebih dahulu.', 'warning')
            return redirect(url_for('admin_login', next=request.path))
        return fn(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {'db_connected': db_ready(), 'current_year': datetime.now().year}


@app.route('/')
def index():
    players = fetch_players(limit=6)
    all_published = fetch_players(limit=500)
    provinces = sorted({p.get('province', '') for p in all_published if p.get('province')})
    stats = {'players': len(all_published), 'provinces': len(provinces), 'stages': len({p.get('stage') for p in all_published if p.get('stage')})}
    return render_template('index.html', players=players, stats=stats)


@app.route('/pemain')
def players_page():
    q = request.args.get('q', '').strip().lower()
    stage = request.args.get('stage', '').strip()
    province = request.args.get('province', '').strip()
    position = request.args.get('position', '').strip()
    all_players = fetch_players(limit=500)
    provinces = sorted({p.get('province', '') for p in all_players if p.get('province')})
    players = [p for p in all_players if
        (not q or q in ' '.join(str(p.get(k, '')) for k in ('name','club','province','position','summary')).lower()) and
        (not stage or p.get('stage') == stage) and (not province or p.get('province') == province) and
        (not position or p.get('position') == position)]
    return render_template('players.html', players=players, provinces=provinces, q=q, stage=stage, province=province, position=position)


@app.route('/pemain/<player_id>')
def player_detail(player_id):
    player = next((p for p in fetch_players(limit=500) if str(p.get('id')) == str(player_id)), None)
    if not player:
        abort(404)
    return render_template('player_detail.html', player=player)


@app.route('/kontribusi', methods=['GET', 'POST'])
def contribute():
    if request.method == 'POST':
        honeypot = request.form.get('website', '').strip()
        if honeypot:
            flash('Terima kasih, kontribusi Anda telah diterima untuk ditinjau.', 'success')
            return redirect(url_for('contribute'))
        name = request.form.get('name', '').strip()
        age_raw = request.form.get('age', '').strip()
        summary = request.form.get('summary', '').strip()
        source_name = request.form.get('source_name', '').strip()
        if not name or not summary or len(summary) < 30:
            flash('Lengkapi nama pemain dan deskripsi minimal 30 karakter.', 'danger')
            return render_template('contribute.html', form=request.form)
        try:
            age = int(age_raw)
            if not 8 <= age <= 45: raise ValueError()
        except ValueError:
            flash('Usia pemain harus antara 8 hingga 45 tahun.', 'danger')
            return render_template('contribute.html', form=request.form)
        source_url = request.form.get('source_url','').strip()
        if source_url and not source_url.lower().startswith(('https://', 'http://')):
            flash('Tautan sumber harus menggunakan http:// atau https://.', 'danger')
            return render_template('contribute.html', form=request.form)
        consent = request.form.get('consent') == 'yes'
        if not consent:
            flash('Persetujuan pengiriman dan verifikasi wajib dicentang.', 'danger')
            return render_template('contribute.html', form=request.form)
        data = {
            'name': name[:120], 'age': age, 'birth_year': datetime.now().year-age,
            'position': request.form.get('position','').strip()[:60],
            'club': request.form.get('club','').strip()[:160],
            'province': request.form.get('province','').strip()[:100],
            'stage': request.form.get('stage','').strip()[:30],
            'summary': summary[:3000], 'source_name': source_name[:120],
            'source_url': source_url[:500],
            'submitter_email': request.form.get('email','').strip()[:254],
            'status': 'pending', 'consent': True,
        }
        if not insert_player(data):
            flash('Kontribusi belum berhasil disimpan. Periksa konfigurasi Supabase atau coba kembali.', 'danger')
            return render_template('contribute.html', form=request.form), 503
        flash('Kontribusi berhasil dikirim! Data akan tampil setelah melewati proses verifikasi admin.', 'success')
        return redirect(url_for('contribute'))
    return render_template('contribute.html', form={})


@app.route('/tentang')
def about():
    return render_template('about.html')


@app.route('/admin/masuk', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        expected_user = os.getenv('ADMIN_USERNAME', 'admin')
        expected_password = os.getenv('ADMIN_PASSWORD', '')
        password_hash = os.getenv('ADMIN_PASSWORD_HASH', '')
        valid_password = check_password_hash(password_hash, password) if password_hash else bool(expected_password) and password == expected_password
        if username == expected_user and valid_password:
            session.clear()
            session['is_admin'] = True
            session['admin_name'] = username
            flash('Berhasil masuk ke panel verifikasi.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Nama pengguna atau kata sandi tidak sesuai.', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/keluar', methods=['POST'])
def admin_logout():
    session.clear()
    flash('Anda telah keluar.', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    submissions = fetch_submissions(limit=300)
    pending = [p for p in submissions if p.get('status') == 'pending']
    return render_template('admin.html', submissions=submissions, pending=pending)


@app.route('/admin/pemain/<player_id>/status', methods=['POST'])
@admin_required
def admin_review(player_id):
    status = request.form.get('status', '')
    note = request.form.get('review_note', '').strip()[:1000]
    if status not in ('published', 'rejected', 'pending'):
        abort(400)
    if update_player_status(player_id, status, note):
        flash('Status kontribusi berhasil diperbarui.', 'success')
    else:
        flash('Status gagal diperbarui. Pastikan kredensial Supabase memiliki izin yang diperlukan.', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/health')
def health():
    return {'status': 'ok', 'database_configured': db_ready()}, 200


@app.errorhandler(404)
def not_found(_error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG') == '1', port=int(os.getenv('PORT', 5000)))
