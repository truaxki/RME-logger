#!/usr/bin/env python3
"""
NAVMED 6470/13 Database Initialization Script

This script creates and initializes the SQLite database for storing
Navy Ionizing Radiation Medical Examination (NAVMED 6470/13) form data.

Usage:
    python init_navmed_database.py [--db-path PATH] [--force]

Options:
    --db-path PATH    Path where the database file should be created
                      (default: ../mcp_patient_intake/data/navmed_radiation_exam.db)
    --force          Overwrite existing database if it exists
"""

import sqlite3
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Default database path relative to this script
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "navmed_radiation_exam.db"

# SQL Schema for NAVMED 6470/13 form
SCHEMA_SQL = """
-- NAVMED 6470/13 Ionizing Radiation Medical Examination Database Schema

-- Main examination record table
CREATE TABLE examinations (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_type VARCHAR(10) CHECK (exam_type IN ('PE', 'RE', 'SE', 'TE')),
    exam_date DATE,
    patient_last_name VARCHAR(100),
    patient_first_name VARCHAR(100),
    patient_middle_initial VARCHAR(5),
    patient_ssn VARCHAR(11), -- Format: XXX-XX-XXXX
    patient_dob DATE,
    command_unit VARCHAR(100),
    rank_grade VARCHAR(20),
    department_service VARCHAR(100),
    facility_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES examining_facilities(facility_id)
);

-- Examining facility information
CREATE TABLE examining_facilities (
    facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_name VARCHAR(200),
    mailing_address TEXT,
    phone_number VARCHAR(20)
);

-- Medical history responses (blocks 3-10)
CREATE TABLE medical_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    personal_history_cancer BOOLEAN,
    history_radiation_exposure BOOLEAN,
    history_anemia_hematuria BOOLEAN,
    history_cancer_therapy BOOLEAN,
    history_radiation_therapy BOOLEAN,
    history_unsealed_sources BOOLEAN,
    history_radiopharmaceutical_therapy BOOLEAN,
    significant_illness_changes BOOLEAN,
    significant_illness_details TEXT,
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Laboratory findings (block 11)
CREATE TABLE laboratory_findings (
    lab_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    evaluation_date DATE,
    hct_result DECIMAL(5,2),
    hct_lab_range VARCHAR(50),
    wbc_result DECIMAL(8,2),
    wbc_lab_range VARCHAR(50),
    wbc_facility VARCHAR(100),
    differential_required BOOLEAN DEFAULT FALSE,
    differential_neutrophils DECIMAL(5,2),
    differential_lymphocytes DECIMAL(5,2),
    differential_monocytes DECIMAL(5,2),
    differential_eosinophils DECIMAL(5,2),
    differential_basophils DECIMAL(5,2),
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Urine testing results (blocks 12a, 12b)
CREATE TABLE urine_tests (
    urine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    dipstick_date DATE,
    dipstick_blood_result VARCHAR(10) CHECK (dipstick_blood_result IN ('Negative', 'Positive', 'Not Performed')),
    microscopic_date DATE,
    rbc_count VARCHAR(50), -- Can be numeric, "0", "negative", "none", "< 2", etc.
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Additional studies (block 13)
CREATE TABLE additional_studies (
    study_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    study_type VARCHAR(100),
    study_date DATE,
    study_results TEXT,
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Physical examination findings (blocks 15-19)
CREATE TABLE physical_examination (
    physical_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    thyroid_status VARCHAR(3) CHECK (thyroid_status IN ('NML', 'ABN', 'NE')),
    breast_status VARCHAR(3) CHECK (breast_status IN ('NML', 'ABN', 'NE')), -- Female ≥ 40
    testes_status VARCHAR(3) CHECK (testes_status IN ('NML', 'ABN', 'NE')),
    dre_status VARCHAR(3) CHECK (dre_status IN ('NML', 'ABN', 'NE')), -- Male ≥ 40
    skin_status VARCHAR(3) CHECK (skin_status IN ('NML', 'ABN', 'NE')),
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Abnormal findings summary (block 14)
CREATE TABLE abnormal_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    finding_description TEXT,
    finding_category VARCHAR(10) CHECK (finding_category IN ('CD', 'NCD')), -- Considered Disqualifying / Not Considered Disqualifying
    basis_for_determination TEXT,
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Assessment and qualification status (blocks 20a, 20b)
CREATE TABLE assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    initial_assessment VARCHAR(3) CHECK (initial_assessment IN ('PQ', 'NPQ')), -- Physically Qualified / Not Physically Qualified
    reab_submitted_date DATE,
    bumed_letter_serial VARCHAR(50),
    bumed_letter_received_date DATE,
    reab_final_determination VARCHAR(3) CHECK (reab_final_determination IN ('PQ', 'NPQ')),
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Signatures and certifications (blocks 21-23)
CREATE TABLE certifications (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    patient_signature_date DATE,
    examiner_name VARCHAR(200),
    examiner_signature_date DATE,
    reviewing_physician_name VARCHAR(200),
    reviewing_physician_signature_date DATE,
    examination_complete_date DATE, -- This is the official completion date per instructions
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id)
);

-- Create indexes for performance
CREATE INDEX idx_examinations_patient ON examinations(patient_last_name, patient_first_name, patient_ssn);
CREATE INDEX idx_examinations_date ON examinations(exam_date);
CREATE INDEX idx_examinations_facility ON examinations(facility_id);
CREATE INDEX idx_medical_history_exam ON medical_history(exam_id);
CREATE INDEX idx_laboratory_findings_exam ON laboratory_findings(exam_id);
CREATE INDEX idx_urine_tests_exam ON urine_tests(exam_id);
CREATE INDEX idx_physical_examination_exam ON physical_examination(exam_id);
CREATE INDEX idx_assessments_exam ON assessments(exam_id);
CREATE INDEX idx_certifications_exam ON certifications(exam_id);
CREATE INDEX idx_abnormal_findings_exam ON abnormal_findings(exam_id);
CREATE INDEX idx_additional_studies_exam ON additional_studies(exam_id);
"""

# Sample data for testing
SAMPLE_DATA_SQL = """
-- Insert sample examining facility
INSERT INTO examining_facilities (facility_name, mailing_address, phone_number) 
VALUES ('Naval Medical Center Portsmouth', '620 John Paul Jones Circle, Portsmouth, VA 23708', '(757) 953-1110');

INSERT INTO examining_facilities (facility_name, mailing_address, phone_number) 
VALUES ('Naval Hospital Camp Lejeune', '100 Brewster Blvd, Camp Lejeune, NC 28547', '(910) 450-4300');

-- Insert sample examination record
INSERT INTO examinations (exam_type, exam_date, patient_last_name, patient_first_name, patient_middle_initial, 
                         patient_ssn, patient_dob, command_unit, rank_grade, department_service, facility_id)
VALUES ('PE', '2024-01-15', 'Smith', 'John', 'A', '123-45-6789', '1985-05-20', 
        'USS Enterprise', 'E-5', 'Nuclear Engineering', 1);

-- Insert sample medical history
INSERT INTO medical_history (exam_id, personal_history_cancer, history_radiation_exposure, history_anemia_hematuria,
                           history_cancer_therapy, history_radiation_therapy, history_unsealed_sources,
                           history_radiopharmaceutical_therapy, significant_illness_changes, significant_illness_details)
VALUES (1, 0, 0, 0, 0, 0, 0, 0, 0, NULL);

-- Insert sample laboratory findings
INSERT INTO laboratory_findings (exam_id, evaluation_date, hct_result, hct_lab_range, wbc_result, wbc_lab_range,
                               wbc_facility, differential_required)
VALUES (1, '2024-01-15', 42.5, '37.0-47.0', 6500, '4500-11000', 'NMCP Lab', 0);

-- Insert sample physical examination
INSERT INTO physical_examination (exam_id, thyroid_status, breast_status, testes_status, dre_status, skin_status)
VALUES (1, 'NML', 'NE', 'NML', 'NE', 'NML');

-- Insert sample assessment
INSERT INTO assessments (exam_id, initial_assessment)
VALUES (1, 'PQ');

-- Insert sample certification
INSERT INTO certifications (exam_id, patient_signature_date, examiner_name, examiner_signature_date,
                          reviewing_physician_name, reviewing_physician_signature_date, examination_complete_date)
VALUES (1, '2024-01-15', 'Dr. Jane Medical', '2024-01-15', 'Dr. Jane Medical', '2024-01-15', '2024-01-15');
"""


def create_database(db_path: Path, force: bool = False, include_sample_data: bool = True) -> bool:
    """
    Create and initialize the NAVMED database.
    
    Args:
        db_path: Path where the database should be created
        force: If True, overwrite existing database
        include_sample_data: If True, insert sample data for testing
        
    Returns:
        True if database was created successfully, False otherwise
    """
    
    # Check if database already exists
    if db_path.exists() and not force:
        print(f"Database already exists at {db_path}")
        print("Use --force to overwrite existing database")
        return False
    
    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Remove existing database if force is True
        if db_path.exists() and force:
            db_path.unlink()
            print(f"Removed existing database: {db_path}")
        
        # Create new database
        print(f"Creating database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Execute schema creation
            print("Creating tables and indexes...")
            conn.executescript(SCHEMA_SQL)
            
            # Insert sample data if requested
            if include_sample_data:
                print("Inserting sample data...")
                conn.executescript(SAMPLE_DATA_SQL)
            
            conn.commit()
            
        print(f"Database created successfully: {db_path}")
        
        # Verify database creation
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Created {len(tables)} tables: {', '.join(tables)}")
            
            if include_sample_data:
                cursor = conn.execute("SELECT COUNT(*) FROM examinations")
                exam_count = cursor.fetchone()[0]
                print(f"Sample data: {exam_count} examination record(s) inserted")
        
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def verify_database(db_path: Path) -> bool:
    """
    Verify that the database exists and has the expected structure.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        True if database is valid, False otherwise
    """
    
    if not db_path.exists():
        print(f"Database does not exist: {db_path}")
        return False
    
    expected_tables = [
        'examinations', 'examining_facilities', 'medical_history',
        'laboratory_findings', 'urine_tests', 'additional_studies',
        'physical_examination', 'abnormal_findings', 'assessments',
        'certifications'
    ]
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                print(f"Missing tables: {', '.join(missing_tables)}")
                return False
            
            print(f"Database verification successful: {len(existing_tables)} tables found")
            return True
            
    except Exception as e:
        print(f"Error verifying database: {e}")
        return False


def main():
    """Main function to handle command line arguments and database creation."""
    
    parser = argparse.ArgumentParser(
        description="Initialize NAVMED 6470/13 database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Database file path (default: {DEFAULT_DB_PATH})"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing database"
    )
    
    parser.add_argument(
        "--no-sample-data",
        action="store_true",
        help="Don't insert sample data"
    )
    
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing database structure"
    )
    
    args = parser.parse_args()
    
    print(f"NAVMED 6470/13 Database Initialization")
    print(f"Database path: {args.db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    if args.verify_only:
        success = verify_database(args.db_path)
    else:
        success = create_database(
            args.db_path, 
            force=args.force,
            include_sample_data=not args.no_sample_data
        )
    
    if success:
        print("\nOperation completed successfully!")
        sys.exit(0)
    else:
        print("\nOperation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
