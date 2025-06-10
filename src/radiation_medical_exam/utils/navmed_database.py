try:
    import sqlcipher3 as sqlite3
    USING_SQLCIPHER = True
except ImportError:
    import sqlite3
    USING_SQLCIPHER = False

import json
from datetime import datetime
from typing import Optional, Any, Dict, List, Union
from pathlib import Path
from contextlib import closing
import logging

logger = logging.getLogger(__name__)

class NavmedDatabase:
    """
    Database interface for NAVMED 6470/13 Ionizing Radiation Medical Examination data.
    
    This class provides structured access to the radiation medical examination database
    following the NAVMED 6470/13 form structure and requirements.
    """
    
    def __init__(self, db_path: str, db_manager=None):
        """Initialize database connection.
        
        Args:
            db_path (str): Path to SQLite database file
            db_manager: Optional encrypted database manager for SQLCipher support
        """
        self.db_path = str(Path(db_path).expanduser())
        self.db_manager = db_manager  # Optional encrypted manager
        self.expected_tables = [
            'examinations', 'examining_facilities', 'medical_history',
            'laboratory_findings', 'urine_tests', 'additional_studies',
            'physical_examination', 'abnormal_findings', 'assessments',
            'certifications'
        ]
        
    def _get_connection(self):
        """Get database connection (encrypted if manager provided)."""
        if self.db_manager:
            # Use encrypted connection
            return self.db_manager.get_connection()
        else:
            # Fallback to regular connection
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            with self._get_connection() as conn:
                with closing(conn.cursor()) as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                        conn.commit()
                        return {"affected_rows": cursor.rowcount, "last_insert_id": cursor.lastrowid}

                    results = [dict(row) for row in cursor.fetchall()]
                    logger.debug(f"Query returned {len(results)} rows")
                    return results
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema information for a specific table"""
        if table_name not in self.expected_tables:
            raise ValueError(f"Table '{table_name}' is not a valid NAVMED table")
        
        try:
            schema_query = f"PRAGMA table_info({table_name})"
            columns = self._execute_query(schema_query)
            
            # Get foreign key information
            fk_query = f"PRAGMA foreign_key_list({table_name})"
            foreign_keys = self._execute_query(fk_query)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
                "description": self._get_table_description(table_name)
            }
        except Exception as e:
            raise Exception(f"Error getting schema for {table_name}: {str(e)}")

    def _get_table_description(self, table_name: str) -> str:
        """Get a description of what each table contains based on NAVMED 6470/13 structure"""
        descriptions = {
            'examinations': 'Main examination record (NAVMED 6470/13 header information)',
            'examining_facilities': 'Medical facilities conducting examinations',
            'medical_history': 'Medical history responses (blocks 3-10 of NAVMED 6470/13)',
            'laboratory_findings': 'Laboratory test results (block 11 - HCT, WBC, differential)',
            'urine_tests': 'Urine testing results (blocks 12a, 12b - dipstick and microscopic)',
            'additional_studies': 'Additional medical studies (block 13)',
            'physical_examination': 'Physical examination findings (blocks 15-19)',
            'abnormal_findings': 'Summary of abnormal findings and recommendations (block 14)',
            'assessments': 'Medical assessment and qualification status (blocks 20a, 20b)',
            'certifications': 'Signatures and certifications (blocks 21-23)'
        }
        return descriptions.get(table_name, "Unknown table")

    def validate_exam_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate examination data before insertion"""
        if table_name not in self.expected_tables:
            return {"valid": False, "errors": [f"Invalid table name: {table_name}"]}
        
        errors = []
        
        # Get table schema for validation
        try:
            schema = self.get_table_schema(table_name)
            required_columns = [col['name'] for col in schema['columns'] if col['notnull'] and col['dflt_value'] is None and col['name'] != 'created_at' and col['name'] != 'updated_at']
            
            # Check for required fields
            missing_required = [col for col in required_columns if col not in data or data[col] is None]
            if missing_required:
                errors.append(f"Missing required fields: {', '.join(missing_required)}")
            
            # Validate data types and constraints
            for column_name, value in data.items():
                if value is not None:
                    column_info = next((col for col in schema['columns'] if col['name'] == column_name), None)
                    if not column_info:
                        errors.append(f"Unknown column: {column_name}")
                        continue
                    
                    # Validate based on NAVMED 6470/13 business rules
                    errors.extend(self._validate_field_value(table_name, column_name, value, column_info))
                    
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_field_value(self, table_name: str, field_name: str, value: Any, column_info: Dict) -> List[str]:
        """Validate specific field values based on NAVMED 6470/13 requirements"""
        errors = []
        
        # Exam type validation (PE, RE, SE, TE)
        if field_name == 'exam_type' and value not in ['PE', 'RE', 'SE', 'TE']:
            errors.append("exam_type must be one of: PE (Physical), RE (Re-examination), SE (Special), TE (Termination)")
        
        # Status field validation (NML, ABN, NE)
        status_fields = ['thyroid_status', 'breast_status', 'testes_status', 'dre_status', 'skin_status']
        if field_name in status_fields and value not in ['NML', 'ABN', 'NE']:
            errors.append(f"{field_name} must be one of: NML (Normal), ABN (Abnormal), NE (Not Examined)")
        
        # Assessment validation (PQ, NPQ)
        if field_name in ['initial_assessment', 'reab_final_determination'] and value not in ['PQ', 'NPQ']:
            errors.append(f"{field_name} must be one of: PQ (Physically Qualified), NPQ (Not Physically Qualified)")
        
        # Finding category validation (CD, NCD)
        if field_name == 'finding_category' and value not in ['CD', 'NCD']:
            errors.append("finding_category must be one of: CD (Considered Disqualifying), NCD (Not Considered Disqualifying)")
        
        # Urine test result validation
        if field_name == 'dipstick_blood_result' and value not in ['Negative', 'Positive', 'Not Performed']:
            errors.append("dipstick_blood_result must be one of: Negative, Positive, Not Performed")
        
        # SSN format validation
        if field_name == 'patient_ssn' and value:
            if not isinstance(value, str) or len(value.replace('-', '')) != 9:
                errors.append("patient_ssn must be in format XXX-XX-XXXX")
        
        return errors

    def add_examination_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add data to any NAVMED examination table with validation"""
        try:
            # Validate data first
            validation = self.validate_exam_data(table_name, data)
            if not validation["valid"]:
                return {"success": False, "errors": validation["errors"]}
            
            # Prepare insert query
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            result = self._execute_query(query, tuple(data.values()))
            
            return {
                "success": True,
                "inserted_id": result["last_insert_id"],
                "affected_rows": result["affected_rows"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_examination_data(self, table_name: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve data from any NAVMED examination table with optional filtering"""
        try:
            base_query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for column, value in filters.items():
                    conditions.append(f"{column} = ?")
                    params.append(value)
                base_query += " WHERE " + " AND ".join(conditions)
            
            base_query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            return self._execute_query(base_query, tuple(params) if params else None)
            
        except Exception as e:
            raise Exception(f"Error retrieving data from {table_name}: {str(e)}")

    def get_complete_examination(self, exam_id: int) -> Dict[str, Any]:
        """Get complete examination data with all related records"""
        try:
            # Get main examination record
            exam_query = "SELECT * FROM examinations WHERE exam_id = ?"
            examination = self._execute_query(exam_query, (exam_id,))
            
            if not examination:
                return {"error": f"Examination with ID {exam_id} not found"}
            
            result = {"examination": examination[0]}
            
            # Get all related records
            related_tables = [
                'medical_history', 'laboratory_findings', 'urine_tests',
                'additional_studies', 'physical_examination', 'abnormal_findings',
                'assessments', 'certifications'
            ]
            
            for table in related_tables:
                query = f"SELECT * FROM {table} WHERE exam_id = ?"
                records = self._execute_query(query, (exam_id,))
                result[table] = records
            
            return result
            
        except Exception as e:
            return {"error": f"Error retrieving complete examination: {str(e)}"}

    def create_complete_examination(self, examination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete examination with all related data"""
        try:
            # Start with main examination record
            if 'examination' not in examination_data:
                return {"success": False, "error": "Missing examination data"}
            
            exam_result = self.add_examination_data('examinations', examination_data['examination'])
            if not exam_result["success"]:
                return {"success": False, "errors": exam_result.get("errors", [exam_result.get("error")])}
            
            exam_id = exam_result["inserted_id"]
            created_records = {"examinations": 1}
            
            # Add related records with the exam_id
            related_sections = [
                'medical_history', 'laboratory_findings', 'urine_tests',
                'additional_studies', 'physical_examination', 'abnormal_findings',
                'assessments', 'certifications'
            ]
            
            for section in related_sections:
                if section in examination_data and examination_data[section]:
                    section_data = examination_data[section].copy()
                    section_data['exam_id'] = exam_id
                    
                    section_result = self.add_examination_data(section, section_data)
                    if section_result["success"]:
                        created_records[section] = 1
                    else:
                        logger.warning(f"Failed to create {section}: {section_result}")
            
            return {
                "success": True,
                "exam_id": exam_id,
                "created_records": created_records
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_examination_summary(self, exam_id: int = None, patient_ssn: str = None) -> Dict[str, Any]:
        """Get a summary of examination(s) for reporting"""
        try:
            if exam_id:
                base_query = """
                    SELECT e.*, f.facility_name, a.initial_assessment, c.examination_complete_date
                    FROM examinations e
                    LEFT JOIN examining_facilities f ON e.facility_id = f.facility_id
                    LEFT JOIN assessments a ON e.exam_id = a.exam_id
                    LEFT JOIN certifications c ON e.exam_id = c.exam_id
                    WHERE e.exam_id = ?
                """
                params = (exam_id,)
            elif patient_ssn:
                base_query = """
                    SELECT e.*, f.facility_name, a.initial_assessment, c.examination_complete_date
                    FROM examinations e
                    LEFT JOIN examining_facilities f ON e.facility_id = f.facility_id
                    LEFT JOIN assessments a ON e.exam_id = a.exam_id
                    LEFT JOIN certifications c ON e.exam_id = c.exam_id
                    WHERE e.patient_ssn = ?
                    ORDER BY e.exam_date DESC
                """
                params = (patient_ssn,)
            else:
                return {"error": "Must provide either exam_id or patient_ssn"}
            
            results = self._execute_query(base_query, params)
            return {"examinations": results}
            
        except Exception as e:
            return {"error": f"Error retrieving examination summary: {str(e)}"} 