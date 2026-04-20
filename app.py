import os, secrets, hashlib, io
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from file_manager import FileManager
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(24))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

file_manager = FileManager()

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'

def format_size(size_bytes):
    if not size_bytes or size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"

app.jinja_env.filters['filesize'] = format_size

TOTAL_CLOUD_SPACE = 5 * 1024 * 1024 * 1024

with app.app_context():
    init_db()
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM users WHERE username = ?", ('admin',)).fetchone()
    if not admin:
        conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                     ('admin', generate_password_hash('admin123'), 'admin'))
        conn.commit()
    conn.close()


@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('admin_dashboard') if is_admin() else url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        login_as = request.form.get('role', 'user')
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            if login_as == 'admin' and user['role'] != 'admin':
                flash('This account does not have admin privileges.', 'error')
                return render_template('login.html')
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['key'] = username.ljust(32)[:32]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return render_template('register.html')
        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('register.html')
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (username, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Username already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
def user_dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))
    if is_admin():
        return redirect(url_for('admin_dashboard'))
    conn = get_db_connection()
    files = conn.execute("SELECT * FROM files WHERE user_id = ? ORDER BY upload_time DESC",
                         (session['user_id'],)).fetchall()
    total_size = conn.execute("SELECT COALESCE(SUM(file_size), 0) as total FROM files WHERE user_id = ?",
                              (session['user_id'],)).fetchone()['total']
    conn.close()
    return render_template('dashboard.html', files=files, total_size=total_size)


@app.route('/upload', methods=['POST'])
def upload_file():
    if not is_logged_in() or is_admin():
        return redirect(url_for('index'))
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('user_dashboard'))
    file = request.files['file']
    content = file.read()
    filename = file.filename
    user_id = session['user_id']
    try:
        parts_meta, file_hash = file_manager.split_and_encrypt_file(content, filename, user_id, session['key'])
        conn = get_db_connection()
        cursor = conn.cursor()
        file_identifier = secrets.token_hex(8)
        cursor.execute("INSERT INTO files (user_id, original_name, file_identifier, file_size, file_hash, storage_mode) VALUES (?,?,?,?,?,?)",
                       (user_id, filename, file_identifier, len(content), file_hash, 'distributed'))
        file_id = cursor.lastrowid
        for part in parts_meta:
            cursor.execute("INSERT INTO file_parts (file_id, part_name, node, sequence_order, size, original_chunk_size) VALUES (?,?,?,?,?,?)",
                           (file_id, part['part_name'], part['node'], part['order'], part['size'], part['original_chunk_size']))
        conn.commit()
        conn.close()
        flash(f'"{filename}" uploaded → split into 3 encrypted chunks → distributed across nodes', 'success')
    except Exception as e:
        flash(f'Upload error: {str(e)}', 'error')
    return redirect(url_for('user_dashboard'))

@app.route('/download/<int:file_id>')
def download_file(file_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    file_info = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_info or file_info['user_id'] != session['user_id']:
        conn.close()
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    parts_meta = conn.execute("SELECT * FROM file_parts WHERE file_id = ? ORDER BY sequence_order", (file_id,)).fetchall()
    conn.close()
    try:
        decrypted = file_manager.decrypt_and_merge_file(file_info['original_name'], file_info['user_id'],
                                                         [dict(p) for p in parts_meta], session['key'])
        if file_info['file_hash']:
            if hashlib.sha256(decrypted).hexdigest() != file_info['file_hash']:
                flash('File integrity check failed!', 'error')
                return redirect(url_for('user_dashboard'))
        return send_file(io.BytesIO(decrypted), download_name=file_info['original_name'], as_attachment=True)
    except Exception as e:
        flash(f'Download error: {str(e)}', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db_connection()
    file_info = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_info or file_info['user_id'] != session['user_id']:
        conn.close()
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    parts_meta = conn.execute("SELECT * FROM file_parts WHERE file_id = ?", (file_id,)).fetchall()
    try:
        file_manager.delete_file_parts(file_info['original_name'], file_info['user_id'], [dict(p) for p in parts_meta])
        conn.execute("DELETE FROM file_parts WHERE file_id = ?", (file_id,))
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        flash(f'"{file_info["original_name"]}" deleted from all nodes.', 'success')
    except Exception as e:
        flash(f'Delete error: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('user_dashboard'))


@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('login'))
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role, created_at FROM users").fetchall()
    total_files = conn.execute("SELECT COUNT(*) as cnt FROM files").fetchone()['cnt']
    total_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']
    total_used = conn.execute("SELECT COALESCE(SUM(file_size), 0) as total FROM files").fetchone()['total']
    user_storage = conn.execute("""
        SELECT u.id, u.username, u.role,
               COUNT(f.id) as file_count,
               COALESCE(SUM(f.file_size), 0) as space_used
        FROM users u LEFT JOIN files f ON u.id = f.user_id
        GROUP BY u.id ORDER BY space_used DESC
    """).fetchall()
    conn.close()
    storage_info = file_manager.get_storage_info()
    free_space = max(0, TOTAL_CLOUD_SPACE - total_used)
    return render_template('admin.html', users=users, user_storage=user_storage,
                           storage_info=storage_info, total_files=total_files,
                           total_users=total_users, total_used=total_used,
                           total_space=TOTAL_CLOUD_SPACE, free_space=free_space)


@app.route('/api/file-info/<int:file_id>')
def api_file_info(file_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    conn = get_db_connection()
    file_info = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_info or file_info['user_id'] != session['user_id']:
        conn.close()
        return jsonify({"error": "Forbidden"}), 403
    parts = conn.execute("SELECT * FROM file_parts WHERE file_id = ? ORDER BY sequence_order", (file_id,)).fetchall()
    conn.close()
    return jsonify({
        "file": {"id": file_info['id'], "name": file_info['original_name'],
                 "size": file_info['file_size'], "size_display": format_size(file_info['file_size']),
                 "hash": file_info['file_hash'], "storage_mode": file_info['storage_mode'],
                 "upload_time": file_info['upload_time']},
        "parts": [{"part_name": p['part_name'], "node": p['node'], "order": p['sequence_order'],
                    "encrypted_size": p['size'], "encrypted_size_display": format_size(p['size']),
                    "original_size": p['original_chunk_size']} for p in parts]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
