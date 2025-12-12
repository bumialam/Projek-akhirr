from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_kampus_z_gen'

# --- KONFIGURASI EMAIL ADMIN (ISI DISINI) ---
EMAIL_PENGIRIM = "bumi.alam05@gmail.com"      # <--- GANTI JADI EMAIL GMAIL KAMU
PASSWORD_APP   = "lqmg xiwh kdnm qxss"    # <--- PASTE 16 DIGIT APP PASSWORD DARI GOOGLE DISINI

# --- DATABASE SEMENTARA ---
data_mahasiswa = [
    {'nim': '10123001', 'nama': 'SITI CYBER', 'jurusan': 'TEKNIK INFORMATIKA', 'ipk': 3.90, 'email': 'email_asli_siti@gmail.com'},
    {'nim': '10123002', 'nama': 'BUDI HACKER', 'jurusan': 'SISTEM INFORMASI', 'ipk': 3.25, 'email': 'email_asli_budi@gmail.com'},
]

# --- DEKORATOR LOGIN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTE LOGIN ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Password Salah Bosku!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- DASHBOARD ---
@app.route('/dashboard')
@login_required
def dashboard():
    total = len(data_mahasiswa)
    rata = round(sum(m['ipk'] for m in data_mahasiswa) / total, 2) if total > 0 else 0
    # Pastikan 'dashboard.html' sesuai nama file di folder templates kamu
    return render_template('dashboard.html', data_list=data_mahasiswa, total=total, rata=rata)

# --- CRUD (TAMBAH, UPDATE, HAPUS) ---
@app.route('/tambah', methods=['POST'])
@login_required
def tambah():
    if any(m['nim'] == request.form['nim'] for m in data_mahasiswa):
        flash('NIM SUDAH ADA!', 'error')
    else:
        data_mahasiswa.append({
            'nim': request.form['nim'],
            'nama': request.form['nama'].upper(),
            'jurusan': request.form['jurusan'].upper(),
            'ipk': float(request.form['ipk']),
            'email': request.form['email']
        })
        flash('DATA BERHASIL DISIMPAN', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update', methods=['POST'])
@login_required
def update():
    nim_lama = request.form['nim_lama']
    for m in data_mahasiswa:
        if m['nim'] == nim_lama:
            m['nim'] = request.form['nim']
            m['nama'] = request.form['nama'].upper()
            m['jurusan'] = request.form['jurusan'].upper()
            m['ipk'] = float(request.form['ipk'])
            m['email'] = request.form['email']
            flash('DATA BERHASIL DIUPDATE', 'success')
            break
    return redirect(url_for('dashboard'))

@app.route('/hapus/<nim>')
@login_required
def hapus(nim):
    global data_mahasiswa
    data_mahasiswa = [m for m in data_mahasiswa if m['nim'] != nim]
    flash('DATA DIHAPUS', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/download')
@login_required
def download():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['NIM', 'NAMA', 'JURUSAN', 'IPK', 'EMAIL'])
    for m in data_mahasiswa: writer.writerow(m.values())
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=data_mahasiswa.csv"})

# --- FITUR KIRIM EMAIL (REAL SMTP) ---
@app.route('/email/<nim>')
@login_required
def kirim_email(nim):
    target = next((m for m in data_mahasiswa if m['nim'] == nim), None)
    
    if target:
        try:
            # 1. Siapkan Pesan Email
            msg = MIMEMultipart()
            msg['From'] = EMAIL_PENGIRIM
            msg['To'] = target['email']
            msg['Subject'] = "Notifikasi Resmi Kampus Z-Gen"

            # Isi Email (Bisa diedit kata-katanya)
            body = f"""
            Halo {target['nama']},
            
            Ini adalah notifikasi otomatis dari sistem Admin.
            Berikut adalah data akademikmu terbaru:
            
            -----------------------------------
            NIM     : {target['nim']}
            Jurusan : {target['jurusan']}
            IPK     : {target['ipk']}
            -----------------------------------
            
            Terus tingkatkan prestasimu!
            
            Salam,
            Admin Kampus Z-Gen
            """
            msg.attach(MIMEText(body, 'plain'))

            # 2. Proses Kirim ke Server Google
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Port khusus SSL
            server.login(EMAIL_PENGIRIM, PASSWORD_APP)       # Login pakai App Password
            server.send_message(msg)                         # Kirim
            server.quit()                                    # Logout

            flash(f'SUKSES! Email terkirim ke {target["email"]}', 'success')
        
        except Exception as e:
            # Kalo gagal (misal internet mati atau password salah)
            print(f"Error: {e}") 
            flash(f'GAGAL KIRIM EMAIL! Cek terminal untuk detail error.', 'error')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)