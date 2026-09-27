import os, sqlite3
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'catalog.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','webp'}
WHATSAPP = '9284248422'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '123456')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute('''CREATE TABLE IF NOT EXISTS cakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price TEXT NOT NULL,
        weight TEXT,
        description TEXT,
        image TEXT,
        available INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    con.commit(); con.close()

def allowed(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def logged_in():
    return session.get('admin_logged_in') is True

@app.route('/')
def index():
    con = db(); cakes = con.execute('SELECT * FROM cakes ORDER BY id DESC').fetchall(); con.close()
    categories = sorted({c['category'] for c in cakes if c['category']})
    return render_template('index.html', cakes=cakes, categories=categories, whatsapp=WHATSAPP)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        flash('Username किंवा Password चुकीचा आहे.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

def require_login():
    if not logged_in(): return redirect(url_for('login'))
    return None

@app.route('/admin')
def admin():
    gate = require_login()
    if gate: return gate
    con = db(); cakes = con.execute('SELECT * FROM cakes ORDER BY id DESC').fetchall(); con.close()
    return render_template('admin.html', cakes=cakes)

@app.route('/admin/add', methods=['POST'])
def add_cake():
    gate = require_login()
    if gate: return gate
    name = request.form.get('name','').strip(); category=request.form.get('category','').strip()
    price=request.form.get('price','').strip(); weight=request.form.get('weight','').strip(); desc=request.form.get('description','').strip()
    image_name=''
    f=request.files.get('image')
    if f and f.filename and allowed(f.filename):
        safe=secure_filename(f.filename); stem,ext=os.path.splitext(safe); image_name=f'{stem}_{os.urandom(4).hex()}{ext.lower()}'
        f.save(os.path.join(UPLOAD_FOLDER,image_name))
    if not name or not category or not price:
        flash('Cake Name, Category आणि Price आवश्यक आहेत.', 'error'); return redirect(url_for('admin'))
    con=db(); con.execute('INSERT INTO cakes(name,category,price,weight,description,image,available) VALUES(?,?,?,?,?,?,1)',(name,category,price,weight,desc,image_name)); con.commit(); con.close()
    flash('Cake successfully added.', 'ok'); return redirect(url_for('admin'))

@app.route('/admin/edit/<int:cake_id>', methods=['GET','POST'])
def edit_cake(cake_id):
    gate=require_login()
    if gate: return gate
    con=db(); cake=con.execute('SELECT * FROM cakes WHERE id=?',(cake_id,)).fetchone()
    if not cake: con.close(); return 'Cake not found',404
    if request.method=='POST':
        name=request.form.get('name','').strip(); category=request.form.get('category','').strip(); price=request.form.get('price','').strip(); weight=request.form.get('weight','').strip(); desc=request.form.get('description','').strip()
        image=cake['image']; f=request.files.get('image')
        if f and f.filename and allowed(f.filename):
            safe=secure_filename(f.filename); stem,ext=os.path.splitext(safe); image=f'{stem}_{os.urandom(4).hex()}{ext.lower()}'; f.save(os.path.join(UPLOAD_FOLDER,image))
        con.execute('UPDATE cakes SET name=?,category=?,price=?,weight=?,description=?,image=? WHERE id=?',(name,category,price,weight,desc,image,cake_id)); con.commit(); con.close()
        flash('Cake updated.', 'ok'); return redirect(url_for('admin'))
    con.close(); return render_template('edit.html', cake=cake)

@app.route('/admin/toggle/<int:cake_id>')
def toggle(cake_id):
    gate=require_login()
    if gate: return gate
    con=db(); con.execute('UPDATE cakes SET available=CASE available WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(cake_id,)); con.commit(); con.close(); return redirect(url_for('admin'))

@app.route('/admin/delete/<int:cake_id>')
def delete_cake(cake_id):
    gate=require_login()
    if gate: return gate
    con=db(); cake=con.execute('SELECT image FROM cakes WHERE id=?',(cake_id,)).fetchone(); con.execute('DELETE FROM cakes WHERE id=?',(cake_id,)); con.commit(); con.close()
    if cake and cake['image']:
        try: os.remove(os.path.join(UPLOAD_FOLDER,cake['image']))
        except OSError: pass
    flash('Cake deleted.', 'ok'); return redirect(url_for('admin'))

@app.route('/health')
def health(): return {'status':'ok'}

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)
