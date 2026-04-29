from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from datetime import datetime
import base64

from config import Config
from utils.database import init_db, create_user, verify_user, verify_admin, save_analysis, get_user_analyses, get_all_analyses, get_all_users, get_risk_distribution
from utils.glacier_analysis import get_detection_overlay, calculate_growth_and_overlay
from utils.gemini_integration import get_risk_solution

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def image_to_base64(image_array):
    _, buffer = cv2.imencode('.jpg', image_array)
    return base64.b64encode(buffer).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if create_user(username, email, password):
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists!', 'error')
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'image1' not in request.files or 'image2' not in request.files:
            flash('Please upload both images!', 'error')
            return redirect(url_for('dashboard'))
        
        file1 = request.files['image1']
        file2 = request.files['image2']
        
        if file1.filename == '' or file2.filename == '':
            flash('Please select both images!', 'error')
            return redirect(url_for('dashboard'))
        
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename1 = secure_filename(f"{session['user_id']}_{timestamp}_1.jpg")
            filename2 = secure_filename(f"{session['user_id']}_{timestamp}_2.jpg")
            
            filepath1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
            
            file1.save(filepath1)
            file2.save(filepath2)
            
            try:
                detection1 = get_detection_overlay(filepath1)
                detection2 = get_detection_overlay(filepath2)
                
                result_image, area1, area2, intersection, growth, growth_percent, growth_status, risk_binary, risk_level = calculate_growth_and_overlay(filepath1, filepath2)
                
                gemini_solution = ""
                if risk_binary == "Risky" or risk_level in ["Medium Risk", "High Risk"]:
                    gemini_solution = get_risk_solution(growth_percent, risk_binary, risk_level, area1, area2, growth_status)
                
                save_analysis(
                    session['user_id'], 
                    filepath1, 
                    filepath2, 
                    area1, 
                    area2, 
                    intersection, 
                    growth, 
                    growth_percent, 
                    growth_status, 
                    risk_binary, 
                    risk_level
                )
                
                image1_b64 = image_to_base64(cv2.imread(filepath1))
                image2_b64 = image_to_base64(cv2.imread(filepath2))
                detection1_b64 = image_to_base64(detection1)
                detection2_b64 = image_to_base64(detection2)
                result_b64 = image_to_base64(result_image)
                
                return render_template('dashboard.html', 
                                     show_results=True,
                                     image1=image1_b64,
                                     image2=image2_b64,
                                     detection1=detection1_b64,
                                     detection2=detection2_b64,
                                     result_image=result_b64,
                                     area1=area1,
                                     area2=area2,
                                     intersection=intersection,
                                     growth=area2-area1,
                                     growth_percent=growth_percent,
                                     growth_status=growth_status,
                                     risk_binary=risk_binary,
                                     risk_level=risk_level,
                                     gemini_solution=gemini_solution)
            
            except Exception as e:
                flash(f'Error processing images: {str(e)}', 'error')
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid file format! Please upload JPG, JPEG, or PNG images.', 'error')
    
    return render_template('dashboard.html', show_results=False)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = verify_admin(username, password)
        if admin:
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    users = get_all_users()
    analyses = get_all_analyses()
    risk_dist = get_risk_distribution()
    
    low_risk = sum(1 for a in analyses if a['risk_level'] == 'Low Risk')
    medium_risk = sum(1 for a in analyses if a['risk_level'] == 'Medium Risk')
    high_risk = sum(1 for a in analyses if a['risk_level'] == 'High Risk')
    
    dummy_locations = []
    for i, analysis in enumerate(analyses[:10]):
        lat = 46.0 + (i * 0.5)
        lon = 7.0 + (i * 0.5)
        
        if analysis['risk_level'] == 'Low Risk':
            color = 'green'
        elif analysis['risk_level'] == 'Medium Risk':
            color = 'orange'
        else:
            color = 'red'
        
        dummy_locations.append({
            'lat': lat,
            'lon': lon,
            'risk_level': analysis['risk_level'],
            'color': color,
            'growth_percent': analysis['growth_percentage'],
            'created_at': analysis['created_at']
        })
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         analyses=analyses,
                         total_analyses=len(analyses),
                         low_risk=low_risk,
                         medium_risk=medium_risk,
                         high_risk=high_risk,
                         locations=dummy_locations)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)