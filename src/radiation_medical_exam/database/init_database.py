"""
Database initialization for NAVMED 6470/13 Radiation Medical Examination system.

This module handles creation and verification of the SQLite database with proper
schema, constraints, and sample data following NAVMED requirements.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def initialize_database(db_path: Path, force: bool = False, include_sample_data: bool = True) -> bool:
    """
    Initialize the NAVMED 6470/13 database with proper schema and optional sample data.
    
    Args:
        db_path: Path to the database file
        force: Whether to overwrite existing database
        include_sample_data: Whether to include sample examination data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        success = create_database(db_path, force=force, include_sample_data=include_sample_data)
        if success:
            logger.info(f"Database successfully initialized at {db_path}")
        return success
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def verify_database(db_path: Path) -> Dict[str, Any]:
    """
    Verify database structure and integrity.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Dict with verification results
    """
    try:
        if not db_path.exists():
            return {"valid": False, "error": "Database file does not exist"}
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check for expected tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'examinations', 'examining_facilities', 'medical_history',
                'laboratory_findings', 'urine_tests', 'additional_studies',
                'physical_examination', 'abnormal_findings', 'assessments',
                'certifications'
            ]
            
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            extra_tables = [t for t in existing_tables if t not in expected_tables and t != 'sqlite_sequence']
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM examinations")
            exam_count = cursor.fetchone()[0]
            
            return {
                "valid": len(missing_tables) == 0,
                "tables_found": len(existing_tables),
                "missing_tables": missing_tables,
                "extra_tables": extra_tables,
                "examination_count": exam_count
            }
            
    except Exception as e:
        return {"valid": False, "error": str(e)}

def create_database(db_path: Path, force: bool = False, include_sample_data: bool = True) -> bool:
    """
    Create the NAVMED database with complete schema.
    
    Args:
        db_path: Path to database file
        force: Whether to overwrite existing database
        include_sample_data: Whether to include sample data
        
    Returns:
        bool: True if successful
    """
    try:
        # Ensure directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle existing database
        if db_path.exists() and not force:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    existing_tables = [row[0] for row in cursor.fetchall()]
                    if existing_tables:
                        logger.warning("Database exists with tables. Use force=True to overwrite.")
                        return False
            except Exception:
                # If we can't read the database, allow recreation
                pass
        
        # Create/recreate database
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Drop existing tables if force mode
            if force:
                _drop_existing_tables(conn)
            
            # Create schema
            _create_schema(conn)
            
            # Add sample data if requested
            if include_sample_data:
                _add_sample_data(conn)
            
            conn.commit()
            logger.info("Database schema created successfully")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False

def _drop_existing_tables(conn: sqlite3.Connection) -> None:
    """Drop existing tables in correct order to respect foreign key constraints."""
    cursor = conn.cursor()
    
    # Get existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    # Drop in reverse dependency order
    drop_order = [
        'certifications', 'assessments', 'abnormal_findings', 'physical_examination',
        'additional_studies', 'urine_tests', 'laboratory_findings', 'medical_history',
        'examinations', 'examining_facilities'
    ]
    
    for table in drop_order:
        if table in existing_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Clean up any other tables that might exist
    for table in existing_tables:
        if table not in drop_order and table != 'sqlite_sequence':
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    logger.info("Existing tables dropped successfully")

def _create_schema(conn: sqlite3.Connection) -> None:
    """Create complete NAVMED database schema."""
    cursor = conn.cursor()
    
    # Examining Facilities table
    cursor.execute("""
        CREATE TABLE examining_facilities (
            facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name TEXT NOT NULL,
            facility_address TEXT,
            facility_phone TEXT,
            facility_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Main Examinations table
    cursor.execute("""
        CREATE TABLE examinations (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_type TEXT NOT NULL CHECK (exam_type IN ('PE', 'RE', 'SE', 'TE')),
            exam_date DATE NOT NULL,
            patient_last_name TEXT NOT NULL,
            patient_first_name TEXT NOT NULL,
            patient_middle_initial TEXT,
            patient_ssn TEXT NOT NULL,
            patient_dob DATE NOT NULL,
            command_unit TEXT,
            rank_grade TEXT,
            department_service TEXT,
            facility_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facility_id) REFERENCES examining_facilities (facility_id)
        )
    """)
    
    # Medical History table (blocks 3-10)
    cursor.execute("""
        CREATE TABLE medical_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            cancer_history TEXT,
            cancer_details TEXT,
            radiation_therapy TEXT,
            radiation_therapy_details TEXT,
            chemotherapy TEXT,
            chemotherapy_details TEXT,
            radioactive_drugs TEXT,
            radioactive_drugs_details TEXT,
            xray_studies TEXT,
            xray_studies_details TEXT,
            nuclear_medicine TEXT,
            nuclear_medicine_details TEXT,
            occupational_exposure TEXT,
            occupational_exposure_details TEXT,
            medical_problems TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Laboratory Findings table (block 11)
    cursor.execute("""
        CREATE TABLE laboratory_findings (
            lab_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            hematocrit REAL,
            hematocrit_normal_range TEXT,
            wbc_count INTEGER,
            wbc_normal_range TEXT,
            differential_neutrophils INTEGER,
            differential_lymphocytes INTEGER,
            differential_monocytes INTEGER,
            differential_eosinophils INTEGER,
            differential_basophils INTEGER,
            other_studies TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Urine Tests table (block 12)
    cursor.execute("""
        CREATE TABLE urine_tests (
            urine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            dipstick_blood_result TEXT CHECK (dipstick_blood_result IN ('Negative', 'Positive', 'Not Performed')),
            microscopic_performed TEXT,
            microscopic_results TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Additional Studies table (block 13)
    cursor.execute("""
        CREATE TABLE additional_studies (
            study_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            study_type TEXT,
            study_date DATE,
            study_results TEXT,
            ordering_physician TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Physical Examination table (blocks 15-19)
    cursor.execute("""
        CREATE TABLE physical_examination (
            physical_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            thyroid_status TEXT CHECK (thyroid_status IN ('NML', 'ABN', 'NE')),
            thyroid_findings TEXT,
            breast_status TEXT CHECK (breast_status IN ('NML', 'ABN', 'NE')),
            breast_findings TEXT,
            testes_status TEXT CHECK (testes_status IN ('NML', 'ABN', 'NE')),
            testes_findings TEXT,
            dre_status TEXT CHECK (dre_status IN ('NML', 'ABN', 'NE')),
            dre_findings TEXT,
            skin_status TEXT CHECK (skin_status IN ('NML', 'ABN', 'NE')),
            skin_findings TEXT,
            additional_findings TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Abnormal Findings table (block 14)
    cursor.execute("""
        CREATE TABLE abnormal_findings (
            finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            finding_description TEXT,
            finding_category TEXT CHECK (finding_category IN ('CD', 'NCD')),
            physician_comments TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Assessments table (blocks 20a, 20b)
    cursor.execute("""
        CREATE TABLE assessments (
            assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            initial_assessment TEXT CHECK (initial_assessment IN ('PQ', 'NPQ')),
            assessment_comments TEXT,
            additional_studies_required TEXT,
            additional_studies_details TEXT,
            reab_referral_required TEXT,
            reab_reason TEXT,
            reab_final_determination TEXT CHECK (reab_final_determination IN ('PQ', 'NPQ')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    # Certifications table (blocks 21-23)
    cursor.execute("""
        CREATE TABLE certifications (
            cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            examining_physician TEXT,
            examining_physician_signature TEXT,
            examination_complete_date DATE,
            reviewing_physician TEXT,
            reviewing_physician_signature TEXT,
            review_date DATE,
            patient_acknowledgment TEXT,
            patient_signature_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES examinations (exam_id)
        )
    """)
    
    logger.info("Database schema created successfully")

def _add_sample_data(conn: sqlite3.Connection) -> None:
    """Add sample examination data for testing."""
    cursor = conn.cursor()
    
    # Add sample facility
    cursor.execute("""
        INSERT INTO examining_facilities (facility_name, facility_address, facility_type)
        VALUES ('Naval Hospital Portsmouth', '620 John Paul Jones Circle, Portsmouth, VA 23708', 'Naval Medical Center')
    """)
    
    # Add sample examination
    cursor.execute("""
        INSERT INTO examinations (
            exam_type, exam_date, patient_last_name, patient_first_name, patient_middle_initial,
            patient_ssn, patient_dob, command_unit, rank_grade, department_service, facility_id
        ) VALUES (
            'PE', '2024-01-15', 'Smith', 'John', 'A', '123-45-6789', '1985-05-20',
            'USS Enterprise', 'E-5', 'Nuclear Engineering', 1
        )
    """)
    
    logger.info("Sample data added successfully") 