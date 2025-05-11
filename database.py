from mysql.connector import connect, Error
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        try:
            # First connect without specifying database
            self.conn = connect(
                host="localhost",
                user="root",  # Replace with your MySQL username
                password="jayanthan$2005",   # Replace with your MySQL password
                auth_plugin='mysql_native_password'
            )
            
            if self.conn.is_connected():
                self.cursor = self.conn.cursor(dictionary=True)
                
                # Create database if it doesn't exist
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS resume_analyzer")
                self.cursor.execute("USE resume_analyzer")
                
                # Create tables
                self.create_tables()
            else:
                raise Error("Failed to connect to MySQL")
                
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            if self.conn is not None and self.conn.is_connected():
                self.conn.close()
            raise Exception("Database connection failed")

    def create_tables(self):
        # Create tables if they don't exist
        create_applicants_table = """
        CREATE TABLE IF NOT EXISTS applicants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            experience VARCHAR(50),
            education VARCHAR(100),
            skills TEXT,
            resume_path VARCHAR(255),
            college VARCHAR(100),
            year_batch VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_hr_table = """
        CREATE TABLE IF NOT EXISTS hr (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_name VARCHAR(100) NOT NULL,
            place VARCHAR(100),
            branch VARCHAR(100),
            logo_path VARCHAR(255),
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            department VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_certifications_table = """
        CREATE TABLE IF NOT EXISTS certifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            name VARCHAR(255) NOT NULL,
            credential_id VARCHAR(255),
            FOREIGN KEY (applicant_id) REFERENCES applicants(id)
        )
        """

        create_jobs_table = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hr_id INT,
            title VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            responsibilities TEXT NOT NULL,
            experience_level VARCHAR(50) NOT NULL,
            education VARCHAR(50) NOT NULL,
            salary_range VARCHAR(100) NOT NULL,
            job_type VARCHAR(50) NOT NULL,
            location VARCHAR(100) NOT NULL,
            deadline DATE NOT NULL,
            skills_required TEXT NOT NULL,
            benefits TEXT,
            status VARCHAR(20) DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (hr_id) REFERENCES hr(id)
        )
        """

        create_applications_table = """
        CREATE TABLE IF NOT EXISTS applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT NOT NULL,
            job_id INT NOT NULL,
            resume_path VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """

        create_saved_jobs_table = """
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT,
            applicant_id INT,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (applicant_id) REFERENCES applicants(id)
        )
        """

        create_education_table = """
        CREATE TABLE IF NOT EXISTS education (
            id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            institution VARCHAR(100),
            degree VARCHAR(100),
            year_start INT,
            year_end INT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id)
        )
        """

        create_experience_table = """
        CREATE TABLE IF NOT EXISTS experience (
            id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            job_title VARCHAR(100),
            company VARCHAR(100),
            year_start INT,
            year_end INT,
            FOREIGN KEY (applicant_id) REFERENCES applicants(id)
        )
        """

        try:
            self.cursor.execute(create_applicants_table)
            self.cursor.execute(create_hr_table)
            self.cursor.execute(create_certifications_table)
            self.cursor.execute(create_jobs_table)
            self.cursor.execute(create_applications_table)
            self.cursor.execute(create_saved_jobs_table)
            self.cursor.execute(create_education_table)
            self.cursor.execute(create_experience_table)
            self.conn.commit()
        except Error as e:
            print(f"Error creating tables: {e}")

    def register_applicant(self, data, resume_path=None):
        try:
            # Hash the password
            hashed_password = generate_password_hash(data['password'])
            
            # Insert applicant data
            query = """
            INSERT INTO applicants (
                name, email, password, phone, experience, education,
                skills, resume_path, college, year_batch
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                data['name'],
                data['email'],
                hashed_password,
                data['phone'],
                data['experience'],
                data['education'],
                data['skills'],
                resume_path,
                data.get('college'),
                data.get('year_batch')
            )
            
            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Error as e:
            print(f"Error registering applicant: {e}")
            self.conn.rollback()
            return None

    def register_hr(self, data, logo_path):
        try:
            hashed_password = generate_password_hash(data['password'])
            
            insert_query = """
            INSERT INTO hr (company_name, place, branch, logo_path, name, 
                          email, password, phone, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data['company_name'], data['place'], data['branch'],
                logo_path, data['name'], data['email'], hashed_password,
                data['phone'], data['department']
            )
            
            self.cursor.execute(insert_query, values)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error registering HR: {e}")
            return False

    def verify_login(self, email, password, role):
        try:
            table = 'applicants' if role == 'applicant' else 'hr'
            query = f"""
                SELECT id, email, password, name
                FROM {table} 
                WHERE LOWER(email) = LOWER(%s)
            """
            
            self.cursor.execute(query, (email,))
            user = self.cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name']
                }
            return None
        except Error as e:
            print(f"Error in verify_login: {e}")
            return None

    def check_email_exists(self, email, role):
        try:
            table = 'applicants' if role == 'applicant' else 'hr'
            query = f"SELECT email FROM {table} WHERE email = %s"
            self.cursor.execute(query, (email,))
            return self.cursor.fetchone() is not None
        except Error as e:
            print(f"Error checking email: {e}")
            return False

    def get_hr_details(self, hr_id):
        try:
            query = "SELECT * FROM hr WHERE id = %s"
            self.cursor.execute(query, (hr_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error getting HR details: {e}")
            return None

    def get_job_stats(self, hr_id):
        try:
            stats = {}
            
            # Active job postings
            self.cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE hr_id = %s AND status = 'Open'", (hr_id,))
            stats['active_jobs'] = self.cursor.fetchone()['count']
            
            # New applications
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM applications a 
                JOIN jobs j ON a.job_id = j.id 
                WHERE j.hr_id = %s AND a.status = 'Pending'
            """, (hr_id,))
            stats['new_applications'] = self.cursor.fetchone()['count']
            
            # Interviews scheduled
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM applications a 
                JOIN jobs j ON a.job_id = j.id 
                WHERE j.hr_id = %s AND a.status = 'Interview Scheduled'
            """, (hr_id,))
            stats['interviews'] = self.cursor.fetchone()['count']
            
            # Positions filled
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM jobs 
                WHERE hr_id = %s AND status = 'Filled'
            """, (hr_id,))
            stats['positions_filled'] = self.cursor.fetchone()['count']
            
            return stats
        except Error as e:
            print(f"Error getting job stats: {e}")
            return None

    def get_recent_activities(self, hr_id, limit=5):
        try:
            query = """
            SELECT 
                'application' as type,
                a.applied_at as timestamp,
                CONCAT(ap.name, ' applied for ', j.title) as description
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN applicants ap ON a.applicant_id = ap.id
            WHERE j.hr_id = %s
            ORDER BY a.applied_at DESC
            LIMIT %s
            """
            self.cursor.execute(query, (hr_id, limit))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting recent activities: {e}")
            return []

    def get_hr_jobs(self, hr_id):
        try:
            query = """
            SELECT j.*, 
                   (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as application_count
            FROM jobs j
            WHERE j.hr_id = %s
            ORDER BY j.created_at DESC
            """
            self.cursor.execute(query, (hr_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting HR jobs: {e}")
            return []

    def add_job(self, hr_id, data):
        try:
            query = """
            INSERT INTO jobs (
                hr_id, title, department, description, requirements, 
                responsibilities, experience_level, education, salary_range, 
                job_type, location, deadline, skills_required, benefits, status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            values = (
                hr_id,
                data.get('title'),
                data.get('department'),
                data.get('description'),
                data.get('requirements'),
                data.get('responsibilities'),
                data.get('experience_level'),
                data.get('education'),
                data.get('salary_range'),
                data.get('job_type'),
                data.get('location'),
                data.get('deadline'),
                data.get('skills_required'),
                data.get('benefits'),
                'Open'  # Default status
            )
            
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error adding job: {e}")
            self.conn.rollback()
            return False

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error executing query: {e}")
            return []

    def save_job(self, applicant_id, job_id):
        try:
            # Check if already saved
            self.cursor.execute(
                "SELECT id FROM saved_jobs WHERE applicant_id = %s AND job_id = %s",
                (applicant_id, job_id)
            )
            if self.cursor.fetchone():
                return True
            
            query = "INSERT INTO saved_jobs (applicant_id, job_id) VALUES (%s, %s)"
            self.cursor.execute(query, (applicant_id, job_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error saving job: {e}")
            return False

    def unsave_job(self, applicant_id, job_id):
        try:
            query = "DELETE FROM saved_jobs WHERE applicant_id = %s AND job_id = %s"
            self.cursor.execute(query, (applicant_id, job_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error unsaving job: {e}")
            return False

    def apply_for_job(self, applicant_id, job_id, resume_path, certificate_paths=None):
        try:
            # Start a transaction
            self.conn.start_transaction()
            
            # Insert application with resume path
            app_query = """
            INSERT INTO applications (
                applicant_id, job_id, resume_path, status, applied_date
            ) VALUES (%s, %s, %s, %s, NOW())
            """
            self.cursor.execute(app_query, (applicant_id, job_id, resume_path, 'Pending'))
            application_id = self.cursor.lastrowid
            
            # Insert certificates if provided
            if certificate_paths:
                cert_query = """
                INSERT INTO application_certificates (
                    application_id, certificate_path, uploaded_date
                ) VALUES (%s, %s, NOW())
                """
                for cert_path in certificate_paths:
                    self.cursor.execute(cert_query, (application_id, cert_path))
            
            self.conn.commit()
            return True
            
        except Error as e:
            print(f"Error applying for job: {e}")
            self.conn.rollback()
            return False

    def get_application(self, applicant_id, job_id):
        try:
            query = """
            SELECT a.*, j.title as job_title 
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.applicant_id = %s AND a.job_id = %s
            """
            self.cursor.execute(query, (applicant_id, job_id))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error getting application: {e}")
            return None

    def get_applicant_applications(self, applicant_id):
        try:
            query = """
            SELECT 
                a.*,
                j.title as job_title,
                j.company_name,
                j.location
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.applicant_id = %s
            ORDER BY a.applied_date DESC
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting applications: {e}")
            return []

    def get_active_jobs(self):
        try:
            query = "SELECT * FROM jobs WHERE status = 'active'"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching active jobs: {e}")
            return []

    def get_saved_jobs(self, applicant_id):
        try:
            query = """
            SELECT j.* FROM saved_jobs sj
            JOIN jobs j ON sj.job_id = j.id
            WHERE sj.applicant_id = %s
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching saved jobs: {e}")
            return []

    def get_applied_jobs(self, applicant_id):
        try:
            query = """
            SELECT j.* FROM jobs j
            JOIN applications a ON j.id = a.job_id
            WHERE a.applicant_id = %s
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting applied jobs: {e}")
            return []

    def get_applicant_stats(self, applicant_id):
        try:
            query = """
                SELECT 
                    COUNT(*) AS applications_sent, 
                    COUNT(DISTINCT interview_id) AS interviews_scheduled 
                FROM applications 
                WHERE applicant_id = %s
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchone() or {}  # Ensure it returns a dictionary
        except Error as e:
            print(f"Error fetching applicant stats: {e}")
            return {}

    def get_recommended_jobs(self, applicant_id):
        try:
            query = "SELECT * FROM jobs WHERE id IN (SELECT job_id FROM recommendations WHERE applicant_id = %s)"
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching recommended jobs: {e}")
            return []

    def get_applicant_details(self, applicant_id):
        try:
            query = """
                SELECT id, name, email, phone, experience, education, 
                       linkedin, portfolio, resume_path, skills
                FROM applicants 
                WHERE id = %s
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error getting applicant details: {e}")
            return None

    def get_applicant_education(self, applicant_id):
        try:
            query = """
                SELECT * FROM education 
                WHERE applicant_id = %s 
                ORDER BY year_end DESC
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting education: {e}")
            return []

    def get_applicant_certifications(self, applicant_id):
        try:
            query = """
                SELECT * FROM certifications 
                WHERE applicant_id = %s
            """
            self.cursor.execute(query, (applicant_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error getting certifications: {e}")
            return []

    def update_hr_settings(self, hr_id, company_name, place, branch, logo_path=None):
        try:
            query = """UPDATE hr SET company_name=%s, place=%s, branch=%s"""
            params = [company_name, place, branch]
            if logo_path:
                query += ", logo_path=%s"
                params.append(logo_path)
            query += " WHERE id=%s"
            params.append(hr_id)
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error updating HR settings: {e}")
            return False

    def get_all_jobs(self):
        try:
            query = "SELECT * FROM jobs WHERE status = 'Open'"  # Adjust based on your schema
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching jobs: {e}")
            return []

    def get_unique_job_locations(self):
        try:
            query = "SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL"
            self.cursor.execute(query)
            return [row['location'] for row in self.cursor.fetchall()]
        except Error as e:
            print(f"Error fetching unique job locations: {e}")
            return []

    def update_hr_logo(self, hr_id, logo_path):
        try:
            query = "UPDATE hr SET logo_path = %s WHERE id = %s"
            self.cursor.execute(query, (logo_path, hr_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error updating HR logo: {e}")
            return False

    def get_job_by_id(self, job_id):
        try:
            query = "SELECT * FROM jobs WHERE id = %s"
            self.cursor.execute(query, (job_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching job: {e}")
            return None

    def get_applicants_by_job_id(self, job_id):
        try:
            query = "SELECT * FROM applicants WHERE job_id = %s"
            self.cursor.execute(query, (job_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching applicants: {e}")
            return []

    def update_applicant_profile(self, applicant_id, headline, location, about, linkedin, portfolio):
        try:
            query = """
            UPDATE applicants
            SET headline = %s, location = %s, about = %s, linkedin = %s, portfolio = %s
            WHERE id = %s
            """
            self.cursor.execute(query, (headline, location, about, linkedin, portfolio, applicant_id))
            self.conn.commit()
        except Error as e:
            print(f"Error updating applicant profile: {e}")

    def add_education(self, applicant_id, institution, degree, year_start, year_end):
        try:
            query = """
            INSERT INTO education (
                applicant_id, institution, degree, year_start, year_end
            ) VALUES (%s, %s, %s, %s, %s)
            """
            values = (applicant_id, institution, degree, year_start, year_end)
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error adding education: {e}")
            self.conn.rollback()
            return False

    def add_experience(self, applicant_id, job_title, company, year_start, year_end):
        try:
            query = """
            INSERT INTO experience (
                applicant_id, job_title, company, year_start, year_end
            ) VALUES (%s, %s, %s, %s, %s)
            """
            values = (applicant_id, job_title, company, year_start, year_end)
            self.cursor.execute(query, values)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error adding experience: {e}")
            self.conn.rollback()
            return False

    def save_hr(self, company_name, place, branch, name, email, password, phone, department, logo_path=None):
        try:
            # Hash the password
            hashed_password = generate_password_hash(password)
            
            # Insert HR data
            insert_query = """
            INSERT INTO hr (company_name, place, branch, logo_path, name, 
                          email, password, phone, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                company_name, place, branch, logo_path, name,
                email, hashed_password, phone, department
            )
            
            self.cursor.execute(insert_query, values)
            self.conn.commit()
            return True
            
        except Error as e:
            print(f"Error saving HR: {e}")
            self.conn.rollback()
            return False

    def check_already_applied(self, applicant_id, job_id):
        try:
            query = """
            SELECT id FROM applications 
            WHERE applicant_id = %s AND job_id = %s
            """
            self.cursor.execute(query, (applicant_id, job_id))
            return self.cursor.fetchone() is not None
        except Error as e:
            print(f"Error checking application: {e}")
            return False

    def add_job_application(self, applicant_id, job_id, resume_path, status):
        try:
            query = """
                INSERT INTO job_applications 
                (applicant_id, job_id, resume_path, status, applied_date) 
                VALUES (%s, %s, %s, %s, NOW())
            """
            values = (applicant_id, job_id, resume_path, status)
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, values)
                    conn.commit()
                    return True
                
        except Exception as e:
            logger.error(f"Error adding job application: {e}")
            return False

    def __del__(self):
        try:
            if hasattr(self, 'cursor') and self.cursor is not None:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn is not None and self.conn.is_connected():
                self.conn.close()
        except Error as e:
            print(f"Error closing database connection: {e}")
