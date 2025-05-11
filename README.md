# Resume Analyzer Application

## Database Setup

The application uses MySQL database with the following configuration:

- Host: localhost
- Database: resume_analyzer
- Default User: root
- Default Password: anand$2005

### Database Setup Instructions

1. Install MySQL Server
2. Create a new user or use root (not recommended for production)
3. Update database credentials in `config.py`
4. The application will automatically create the database and required tables on startup

## Database Schema

CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hr_id INT,
    title VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    responsibilities TEXT,
    experience_level VARCHAR(50),
    education VARCHAR(100),
    salary_range VARCHAR(100),
    job_type VARCHAR(50),
    location VARCHAR(100) NOT NULL,
    deadline DATE,
    skills_required TEXT,
    benefits TEXT,
    status VARCHAR(20) DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hr_id) REFERENCES hr(id)
)
