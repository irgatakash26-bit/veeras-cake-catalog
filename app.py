import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
WHATSAPP = '9284248422'

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_BUCKET = 'cake-images'

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError('SUPABASE_URL and SUPABASE_KEY are required in .env')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '123456')

def allowed(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def logged_in():
    return session.get('admin_logged_in') is True

def require_login():
    if not logged_in():
        return redirect(url_for('login'))
    return None

def get_cakes():
    result = (
        supabase
        .table('cakes')
        .select('*')
        .order('id', desc=True)
        .execute()
    )
    return result.data or []

def get_cake(cake_id):
    result = (
        supabase
        .table('cakes')
        .select('*')
        .eq('id', cake_id)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None

def upload_image(file):
    if not file or not file.filename or not allowed(file.filename):
        return ''

    safe = secure_filename(file.filename)
    stem, ext = os.path.splitext(safe)

    filename = f'{stem}_{os.urandom(4).hex()}{ext.lower()}'

    file_bytes = file.read()

    supabase.storage.from_('cake-images').upload(
        filename,
        file_bytes,
        {
            'content-type': file.mimetype or 'application/octet-stream',
            'upsert': 'true'
        }
    )

    return supabase.storage.from_('cake-images').get_public_url(filename)

def delete_image(image_url):
    if not image_url:
        return

    marker = '/storage/v1/object/public/cake-images/'

    if marker in image_url:
        filename = image_url.split(marker, 1)[1]

        try:
            supabase.storage.from_('cake-images').remove([filename])
        except Exception:
            pass

@app.route('/')
def index():
    cakes = get_cakes()

    categories = sorted({
        c.get('category')
        for c in cakes
        if c.get('category')
    })

    return render_template(
        'index.html',
        cakes=cakes,
        categories=categories,
        whatsapp=WHATSAPP
    )

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        if (
            request.form.get('username') == ADMIN_USER
            and request.form.get('password') == ADMIN_PASSWORD
        ):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))

        flash('Username किंवा Password चुकीचा आहे.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():

    gate = require_login()

    if gate:
        return gate

    cakes = get_cakes()

    return render_template(
        'admin.html',
        cakes=cakes
    )

@app.route('/admin/add', methods=['POST'])
def add_cake():

    gate = require_login()

    if gate:
        return gate

    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price = request.form.get('price', '').strip()
    weight = request.form.get('weight', '').strip()
    description = request.form.get('description', '').strip()

    if not name or not category or not price:

        flash(
            'Cake Name, Category आणि Price आवश्यक आहेत.',
            'error'
        )

        return redirect(url_for('admin'))

    image_url = ''

    file = request.files.get('image')

    try:

        if file and file.filename and allowed(file.filename):
            image_url = upload_image(file)

        supabase.table('cakes').insert({
            'name': name,
            'category': category,
            'price': price,
            'weight': weight,
            'description': description,
            'image': image_url,
            'available': True
        }).execute()

        flash('Cake successfully added.', 'ok')

    except Exception as e:

        if image_url:
            delete_image(image_url)

        flash(f'Cake add failed: {e}', 'error')

    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:cake_id>', methods=['GET', 'POST'])
def edit_cake(cake_id):

    gate = require_login()

    if gate:
        return gate

    cake = get_cake(cake_id)

    if not cake:
        return 'Cake not found', 404

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        weight = request.form.get('weight', '').strip()
        description = request.form.get('description', '').strip()

        if not name or not category or not price:

            flash(
                'Cake Name, Category आणि Price आवश्यक आहेत.',
                'error'
            )

            return redirect(
                url_for('edit_cake', cake_id=cake_id)
            )

        old_image = cake.get('image') or ''
        image_url = old_image

        file = request.files.get('image')

        try:

            if file and file.filename and allowed(file.filename):
                image_url = upload_image(file)

            supabase.table('cakes').update({
                'name': name,
                'category': category,
                'price': price,
                'weight': weight,
                'description': description,
                'image': image_url
            }).eq(
                'id',
                cake_id
            ).execute()

            if image_url != old_image and old_image:
                delete_image(old_image)

            flash('Cake updated.', 'ok')

        except Exception as e:

            if image_url != old_image and image_url:
                delete_image(image_url)

            flash(
                f'Cake update failed: {e}',
                'error'
            )

        return redirect(url_for('admin'))

    return render_template(
        'edit.html',
        cake=cake
    )

@app.route('/admin/toggle/<int:cake_id>')
def toggle(cake_id):

    gate = require_login()

    if gate:
        return gate

    cake = get_cake(cake_id)

    if cake:

        new_status = not bool(
            cake.get('available', True)
        )

        supabase.table('cakes').update({
            'available': new_status
        }).eq(
            'id',
            cake_id
        ).execute()

    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:cake_id>')
def delete_cake(cake_id):

    gate = require_login()

    if gate:
        return gate

    cake = get_cake(cake_id)

    if cake:

        try:

            supabase.table('cakes').delete().eq(
                'id',
                cake_id
            ).execute()

            delete_image(
                cake.get('image') or ''
            )

            flash('Cake deleted.', 'ok')

        except Exception as e:

            flash(
                f'Cake delete failed: {e}',
                'error'
            )

    return redirect(url_for('admin'))

@app.route('/health')
def health():

    try:

        supabase.table('cakes').select(
            'id'
        ).limit(1).execute()

        return {
            'status': 'ok',
            'database': 'supabase'
        }

    except Exception as e:

        return {
            'status': 'error',
            'database': 'supabase',
            'message': str(e)
        }, 500

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )