from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
from database import Database
from datetime import datetime
import logging
import time
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Replace with a secure secret key

# Configure upload folders
UPLOAD_FOLDER = 'static/uploads'
RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
LOGO_FOLDER = os.path.join(UPLOAD_FOLDER, 'logos')
ALLOWED_EXTENSIONS = {'pdf'}

# Create upload directories if they don't exist
os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

try:
    db = Database()
except Exception as e:
    print(f"Failed to initialize database: {e}")
    exit(1)

# Add logging for better debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')

            if not all([email, password, role]):
                return jsonify({
                    'success': False,
                    'message': 'Please fill in all fields'
                })

            user = db.verify_login(email, password, role)
            
            if user:
                session['user_id'] = user['id']
                session['role'] = role
                redirect_url = url_for('applicant_dashboard') if role == 'applicant' else url_for('hr_dashboard')
                
                logger.debug(f"User: {user}, Redirect URL: {redirect_url}")
                
                return jsonify({
                    'success': True,
                    'redirect': redirect_url
                })

            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            })

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred during login'
            })

    return render_template('login.html')

@app.route('/register_applicant', methods=['GET', 'POST'])
def register_applicant():
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'phone': request.form.get('phone'),
                'experience': request.form.get('experience'),
                'education': request.form.get('education'),
                'skills': request.form.get('skills'),
                'college': request.form.get('college'),
                'year_batch': request.form.get('year_batch')
            }

            # Debug print
            print("Received form data:", data)

            # Validate required fields
            required_fields = ['name', 'email', 'password', 'phone']
            for field in required_fields:
                if not data.get(field):
                    flash(f'{field.capitalize()} is required')
                    return redirect(url_for('register_applicant'))

            # Check if email already exists
            if db.check_email_exists(data['email'], 'applicant'):
                flash('Email already registered')
                return redirect(url_for('register_applicant'))

            # Handle resume file upload
            resume_path = None
            if 'resume' in request.files:
                resume_file = request.files['resume']
                if resume_file.filename != '' and allowed_file(resume_file.filename):
                    resume_filename = secure_filename(f"{data['email']}_{int(time.time())}.pdf")
                    resume_path = os.path.join(RESUME_FOLDER, resume_filename)
                    resume_file.save(resume_path)
                    data['resume_path'] = resume_path

            # Register applicant
            applicant_id = db.register_applicant(data, resume_path)
            if not applicant_id:
                flash('Registration failed. Please try again.')
                return redirect(url_for('register_applicant'))

            flash('Registration successful! Please login.')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Registration error: {str(e)}")
            flash(f'An error occurred: {str(e)}')
            return redirect(url_for('register_applicant'))

    return render_template('register_applicant.html')

@app.route('/register_hr', methods=['GET', 'POST'])
def register_hr():
    if request.method == 'POST':
        try:
            # Check if email already exists
            email = request.form.get('email')
            if db.check_email_exists(email, 'hr'):
                flash('Email already registered. Please use a different email.')
                return redirect(url_for('register_hr'))

            # Handle logo upload
            logo = request.files.get('logo')
            if logo:
                logo_filename = secure_filename(logo.filename)
                logo_path = os.path.join(LOGO_FOLDER, logo_filename)
                logo.save(logo_path)
            else:
                logo_path = None  # Handle case where no logo is uploaded

            # Get form data
            company_name = request.form.get('company_name')
            place = request.form.get('place')
            branch = request.form.get('branch')
            name = request.form.get('name')
            password = request.form.get('password')
            phone = request.form.get('phone')
            department = request.form.get('department')

            # Save HR details to the database
            if db.save_hr(company_name, place, branch, name, email, password, phone, department, logo_path):
                flash('HR registered successfully!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            print(f"Error in register_hr: {str(e)}")  # Debug print
        
        return redirect(url_for('register_hr'))
    
    return render_template('register_hr.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Protected routes
@app.route('/applicant_dashboard')
def applicant_dashboard():
    if 'user_id' not in session or session['role'] != 'applicant':
        return redirect(url_for('login'))
    
    applicant_id = session['user_id']
    applicant = db.get_applicant_details(applicant_id)

    # Ensure applicant data is valid
    if not applicant:
        flash('Applicant not found. Please log in again.')
        return redirect(url_for('login'))

    # Fetch all jobs listed by HR
    jobs = db.get_all_jobs()  # Ensure this method is implemented correctly

    # Fetch unique locations for the filter
    locations = db.get_unique_job_locations()  # New method to fetch unique locations

    # Fetch applicant statistics
    stats = db.get_applicant_stats(applicant_id) or {}  # Provide a default empty dictionary

    # Ensure saved_jobs is defined
    saved_jobs = db.get_saved_jobs(applicant_id) or []  # Fetch saved jobs or provide an empty list

    # Ensure applied_jobs is defined
    applied_jobs = db.get_applied_jobs(applicant_id) or []  # Fetch applied jobs or provide an empty list

    logger.debug(f"Applicant: {applicant}, Jobs: {jobs}, Locations: {locations}, Stats: {stats}, Saved Jobs: {saved_jobs}, Applied Jobs: {applied_jobs}")

    return render_template('applicant_dashboard.html', applicant=applicant, jobs=jobs, locations=locations, stats=stats, saved_jobs=saved_jobs, applied_jobs=applied_jobs)

@app.route('/hr_dashboard')
def hr_dashboard():
    if 'user_id' not in session or session['role'] != 'hr':
        return redirect(url_for('login'))
    
    hr_id = session['user_id']
    hr_details = db.get_hr_details(hr_id)

    if not hr_details:
        session.clear()
        flash('Error loading HR details. Please login again.')
        return redirect(url_for('login'))
    
    job_stats = db.get_job_stats(hr_id) or {}  # Provide a default empty dictionary
    recent_activities = db.get_recent_activities(hr_id) or []  # Provide a default empty list
    jobs = db.get_hr_jobs(hr_id) or []  # Provide a default empty list
    
    return render_template('hr_dashboard.html',
                         hr_details=hr_details,
                         job_stats=job_stats,
                         recent_activities=recent_activities,
                         jobs=jobs)

@app.route('/add_job', methods=['POST'])
def add_job():
    if 'user_id' not in session or session['role'] != 'hr':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        # Get all form data
        data = {
            'title': request.form.get('title'),
            'department': request.form.get('department'),
            'description': request.form.get('description'),
            'requirements': request.form.get('requirements'),
            'responsibilities': request.form.get('responsibilities'),
            'experience_level': request.form.get('experience_level'),
            'education': request.form.get('education'),
            'salary_range': request.form.get('salary_range'),
            'job_type': request.form.get('job_type'),
            'location': request.form.get('location'),
            'deadline': request.form.get('deadline'),
            'skills_required': request.form.get('skills_required'),
            'benefits': request.form.get('benefits')
        }

        # Validate required fields
        required_fields = ['title', 'department', 'description', 'location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Add the job
        if db.add_job(session['user_id'], data):
            return jsonify({
                'success': True, 
                'message': 'Job posted successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to post job'
            }), 500

    except Exception as e:
        logger.error(f"Error adding job: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/get_job/<int:job_id>', methods=['GET'])
def get_job(job_id):
    try:
        job = db.get_job_by_id(job_id)  # Implement this method in your database class
        if job:
            return jsonify(job)
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def calculate_match_percentage(applicant_skills, job_skills):
    job_skills_set = set(job_skills.split(','))
    applicant_skills_set = set(applicant_skills.split(','))
    matching_skills = applicant_skills_set.intersection(job_skills_set)
    return (len(matching_skills) / len(job_skills_set)) * 100 if job_skills_set else 0

@app.route('/view-applicants/<int:job_id>')
def view_applicants(job_id):
    applicants = db.get_applicants_by_job_id(job_id)  # Use the correct method name
    job = db.get_job_by_id(job_id)  # Fetch job details

    if job is None:
        return "Job not found", 404

    for applicant in applicants:
        applicant.match_percentage = calculate_match_percentage(applicant.skills, job.skills_required)

    return render_template('view_applicants.html', applicants=applicants, job=job)
        
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    # Handle resume upload and analysis
    pass

@app.route('/hr/settings', methods=['GET'])
def hr_settings():
    if 'user_id' not in session or session['role'] != 'hr':
        return redirect(url_for('login'))
    
    hr_id = session['user_id']
    hr_details = db.get_hr_details(hr_id)
    
    if not hr_details:
        flash('Error loading HR details')
        return redirect(url_for('hr_dashboard'))
    
    return render_template('hr_settings.html', hr_details=hr_details)

@app.route('/hr/update_settings', methods=['POST'])
def update_hr_settings():
    if 'user_id' not in session or session['role'] != 'hr':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    hr_id = session['user_id']
    name = request.form.get('name')
    company_name = request.form.get('company_name')
    place = request.form.get('place')
    branch = request.form.get('branch')
    phone = request.form.get('phone')
    department = request.form.get('department')

    # Ensure all required fields are present
    if not all([name, company_name, place, branch, phone, department]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if db.update_hr_settings(hr_id, name, company_name, place, branch, phone, department):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Failed to update settings'})

@app.route('/hr/update_password', methods=['POST'])
def update_hr_password():
    if 'user_id' not in session or session['role'] != 'hr':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        
        if db.update_hr_password(session['user_id'], old_password, new_password):
            return jsonify({'success': True, 'message': 'Password updated successfully'})
        return jsonify({'success': False, 'message': 'Invalid current password'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/hr/update_logo', methods=['POST'])
def update_hr_logo():
    if 'user_id' not in session or session['role'] != 'hr':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
            
        logo = request.files['logo']
        if logo and allowed_file(logo.filename):
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(logo.filename)}"
            logo_path = os.path.join(LOGO_FOLDER, filename)
            logo.save(logo_path)
            
            if db.update_hr_logo(session['user_id'], logo_path):
                return jsonify({'success': True, 'message': 'Logo updated successfully'})
        return jsonify({'success': False, 'message': 'Invalid file type'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/hr/update_profile', methods=['POST'])
def update_hr_profile():
    if 'user_id' not in session or session['role'] != 'hr':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        logo_path = None
        if 'logo' in request.files and request.files['logo'].filename != '':
            logo = request.files['logo']
            if logo and allowed_file(logo.filename):
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(logo.filename)}"
                logo_path = os.path.join(LOGO_FOLDER, filename)
                logo.save(logo_path)
        
        company_name = request.form.get('company_name')
        place = request.form.get('place')
        branch = request.form.get('branch')
        
        # Log the received data for debugging
        logger.debug(f"Updating profile for HR ID: {session['user_id']}, Company Name: {company_name}, Place: {place}, Branch: {branch}, Logo Path: {logo_path}")
        
        if db.update_hr_settings(session['user_id'], company_name, place, branch, logo_path):
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        return jsonify({'success': False, 'message': 'Failed to update profile'})
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'success': False, 'message': str(e)})

# Additional routes for job management and applications

@app.route('/save-job/<int:job_id>', methods=['POST'])
def save_job(job_id):
    if 'user_id' not in session or session['role'] != 'applicant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if db.save_job(session['user_id'], job_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Failed to save job'})
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/unsave-job/<int:job_id>', methods=['POST'])
def unsave_job(job_id):
    if 'user_id' not in session or session['role'] != 'applicant':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        if db.unsave_job(session['user_id'], job_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Failed to unsave job'})
    except Exception as e:
        logger.error(f"Error unsaving job: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/apply-job/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session or session['role'] != 'applicant':
        return jsonify({'success': False, 'message': 'Please login as an applicant'})
    
    try:
        if request.method == 'POST':
            if 'resume' not in request.files:
                return jsonify({'success': False, 'message': 'No resume file uploaded'})
            
            resume = request.files['resume']
            if resume.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})
            
            if resume and allowed_file(resume.filename):
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"resume_{session['user_id']}_{job_id}_{timestamp}.pdf"
                resume_path = os.path.join(RESUME_FOLDER, filename)
                
                # Save the file
                resume.save(resume_path)
                
                # Store resume path in session for certificate verification step
                session['temp_resume_path'] = resume_path
                session['temp_job_id'] = job_id
                
                # Redirect to certificate verification page
                return jsonify({
                    'success': True,
                    'redirect': f'/verify-certificates/{job_id}'
                })
            
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Please upload a PDF.'
            })
            
        # GET request - show application form
        job = db.get_job_by_id(job_id)
        if not job:
            return "Job not found", 404
        return render_template('job_application.html', job=job)
        
    except Exception as e:
        logger.error(f"Error in apply_job: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        })

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        headline = request.form.get('headline')
        location = request.form.get('location')
        about = request.form.get('about')
        linkedin = request.form.get('linkedin')
        portfolio = request.form.get('portfolio')

        # Update the applicant's profile in the database
        db.update_applicant_profile(session['user_id'], headline, location, about, linkedin, portfolio)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the applicant's profile details from the database
    applicant_id = session['user_id']
    applicant = db.get_applicant_details(applicant_id)

    if not applicant:
        flash('Applicant not found. Please log in again.')
        return redirect(url_for('login'))

    return render_template('profile.html', applicant=applicant)

@app.route('/add_skill', methods=['POST'])
def add_skill():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        skill = request.json.get('skill')
        db.add_skill(session['user_id'], skill)  # Implement this method in your database class
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/remove_skill', methods=['POST'])
def remove_skill():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        skill = request.json.get('skill')
        db.remove_skill(session['user_id'], skill)  # Implement this method in your database class
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/job/<int:job_id>', methods=['GET'])
def job_details(job_id):
    try:
        job = db.get_job_by_id(job_id)
        if job:
            return jsonify(job)
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/applications')
def view_applications():
    if 'user_id' not in session or session['role'] != 'applicant':
        return redirect(url_for('login'))
    
    try:
        applicant_id = session['user_id']
        # Get applied jobs with their status
        applied_jobs = db.get_applied_jobs(applicant_id)
        return render_template('applications.html', applications=applied_jobs)
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        flash('Error loading applications')
        return redirect(url_for('applicant_dashboard'))

@app.route('/saved-jobs')
def saved_jobs():
    if 'user_id' not in session or session['role'] != 'applicant':
        return redirect(url_for('login'))
    
    try:
        applicant_id = session['user_id']
        saved_jobs = db.get_saved_jobs(applicant_id)
        return render_template('saved_jobs.html', saved_jobs=saved_jobs)
    except Exception as e:
        logger.error(f"Error fetching saved jobs: {e}")
        flash('Error loading saved jobs')
        return redirect(url_for('applicant_dashboard'))

@app.route('/job/<int:job_id>')
def job_description(job_id):
    job = db.get_job_by_id(job_id)  # Fetch job details from the database
    applicant = db.get_applicant_by_id(session['user_id'])  # Fetch applicant details

    if job is None:
        return "Job not found", 404

    return render_template('job_description.html', job=job, applicant=applicant)

@app.route('/verify-certificates/<int:job_id>', methods=['GET', 'POST'])
def verify_certificates(job_id):
    if 'user_id' not in session or session['role'] != 'applicant':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Handle certificate uploads
            certificate_data = []
            certificate_files = request.files.getlist('certificate_file[]')
            certificate_names = request.form.getlist('certificate_name[]')
            issuing_orgs = request.form.getlist('issuing_organization[]')
            issue_dates = request.form.getlist('issue_date[]')
            
            for i, cert_file in enumerate(certificate_files):
                if cert_file and allowed_file(cert_file.filename):
                    # Create unique filename for each certificate
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = secure_filename(f"cert_{session['user_id']}_{timestamp}_{cert_file.filename}")
                    cert_path = os.path.join(RESUME_FOLDER, filename)
                    cert_file.save(cert_path)
                    
                    certificate_data.append({
                        'name': certificate_names[i],
                        'organization': issuing_orgs[i],
                        'issue_date': issue_dates[i],
                        'file_path': cert_path
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid file type. Please upload PDF files only.'
                    })
            
            # Store certificate data in session for verification
            session['temp_certificates'] = certificate_data
            
            return jsonify({
                'success': True,
                'message': 'Certificates uploaded successfully'
            })
            
        except Exception as e:
            logger.error(f"Error in certificate upload: {e}")
            return jsonify({
                'success': False,
                'message': 'An error occurred. Please try again.'
            })
    
    # GET request - show certificate upload form
    job = db.get_job_by_id(job_id)
    return render_template('verify_certificates.html', job=job)

@app.route('/verify-certificate-authenticity/<int:job_id>', methods=['GET', 'POST'])
def verify_certificate_authenticity(job_id):
    if 'user_id' not in session or session['role'] != 'applicant':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Simulate API verification with dummy data
            verification_results = []
            certificate_names = request.form.getlist('certificate_name[]')
            issuing_orgs = request.form.getlist('issuing_organization[]')
            
            for i in range(len(certificate_names)):
                # Dummy verification logic
                is_verified = True if i % 2 == 0 else False  # Alternates between true/false
                verification_results.append({
                    'certificate_name': certificate_names[i],
                    'issuing_organization': issuing_orgs[i],
                    'is_verified': is_verified,
                    'verification_date': datetime.now().strftime('%Y-%m-%d'),
                    'verification_id': f"VERIFY-{random.randint(1000, 9999)}"
                })
            
            # Store verification results in session for final submission
            session['verification_results'] = verification_results
            
            return jsonify({
                'success': True,
                'verification_results': verification_results,
                'redirect': url_for('applications')
            })
            
        except Exception as e:
            logger.error(f"Error in certificate verification: {e}")
            return jsonify({
                'success': False,
                'message': 'Verification failed. Please try again.'
            })
    
    # GET request - show verification results page
    certificates = session.get('temp_certificates', [])
    return render_template('verify_certificate_authenticity.html', 
                         job_id=job_id, 
                         certificates=certificates)

if __name__ == '__main__':
    app.run(debug=True)
