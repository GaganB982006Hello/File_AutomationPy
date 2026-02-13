from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import os
import email_sorter
import file_organizer
import image_resizer
import pdf_merger
import web_scraper
from flask_login import LoginManager, UserMixin, login_required, current_user
from db import log_activity, get_user_by_id, get_user_history, get_all_users, get_all_history
from auth import auth_bp
from extensions import init_oauth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Initialize OAuth
init_oauth(app)

# Register Auth Blueprint
app.register_blueprint(auth_bp)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.name = user_data['name']
        self.email = user_data['email']
        self.role = user_data.get('role', 'user')

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    history = get_user_history(current_user.id)
    return render_template('dashboard.html', history=history)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash("Access Denied: You are not an admin.", "error")
        return redirect(url_for('index'))
    
    users = get_all_users()
    history = get_all_history()
    return render_template('admin.html', users=users, history=history)

@app.route('/email-sorter', methods=['GET', 'POST'])
@login_required
def email_sorter_route():
    result = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        server = request.form['server']
        query = request.form['query']
        folder = request.form['folder']
        
        result = email_sorter.sort_emails(email, password, server, query, folder)
        flash(result)
        log_activity(current_user.id, "Email Sorter", f"Sorted emails for {email}")
        
    return render_template('email_sorter.html', result=result)

@app.route('/file-organizer', methods=['GET', 'POST'])
@login_required
def file_organizer_route():
    result = None
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files uploaded')
            return redirect(request.url)
            
        files = request.files.getlist('files')
        
        # files is a list of FileStorage objects
        # if user selects nothing, browser submits an empty part without filename
        if not files or files[0].filename == '':
             flash('No files selected')
             return redirect(request.url)

        output_path, message = file_organizer.organize_files(files)
        
        if output_path:
             flash(message)
             log_activity(current_user.id, "File Organizer", f"Organized {len(files)} files", "organized_files.zip")
             return send_file(output_path, as_attachment=True, download_name='organized_files.zip')
        else:
             flash(message) # Error message
        
    return render_template('file_organizer.html', result=result)

@app.route('/image-resizer', methods=['GET', 'POST'])
@login_required
def image_resizer_route():
    result = None
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No images uploaded')
            return redirect(request.url)
            
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
             flash('No images selected')
             return redirect(request.url)

        try:
            width = int(request.form['width'])
            output_path, message = image_resizer.resize_images(files, width)
            
            if output_path:
                flash(message)
                log_activity(current_user.id, "Image Resizer", f"Resized {len(files)} images to width {width}", "resized_images.zip")
                return send_file(output_path, as_attachment=True, download_name='resized_images.zip')
            else:
                flash(message)
        except ValueError:
            flash("Error: Invalid width.")
        
    return render_template('image_resizer.html', result=result)

@app.route('/pdf-merger', methods=['GET', 'POST'])
@login_required
def pdf_merger_route():
    result = None
    if request.method == 'POST':
         if 'files' not in request.files:
            flash('No PDFs uploaded')
            return redirect(request.url)
            
         files = request.files.getlist('files')
         output_name = request.form['output_name']
         
         if not files or files[0].filename == '':
             flash('No PDFs selected')
             return redirect(request.url)

         output_path, message = pdf_merger.merge_pdfs(files, output_name)
         
         if output_path:
             flash(message)
             log_activity(current_user.id, "PDF Merger", f"Merged {len(files)} PDFs", output_name)
             return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))
         else:
             flash(message)
        
    return render_template('pdf_merger.html', result=result)

@app.route('/web-scraper', methods=['GET', 'POST'])
@login_required
def web_scraper_route():
    result = None
    if request.method == 'POST':
        url = request.form['url']
        # No input folder needed anymore
        
        output_path, message = web_scraper.scrape_data(url)
        
        if output_path:
            flash(message)
            log_activity(current_user.id, "Web Scraper", f"Scraped data from {url}", "Scraped_Data.xlsx")
            return send_file(output_path, as_attachment=True, download_name='Scraped_Data.xlsx')
        else:
            flash(message)
        
    return render_template('web_scraper.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
