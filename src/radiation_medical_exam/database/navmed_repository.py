"""
Repository pattern for NAVMED 6470/13 database operations.

This module provides a clean interface for database operations with proper
separation of concerns and validation.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Any, Dict, List, Union
from pathlib import Path
from contextlib import closing
import logging

logger = logging.getLogger(__name__)

class NavmedRepository:
    """
    Repository for NAVMED 6470/13 database operations.
    
    Provides clean, validated access to radiation medical examination data
    following the repository pattern for better testability and maintainability.
    """
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize repository with database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = str(Path(db_path).expanduser())
        self.expected_tables = [
            'examinations', 'examining_facilities', 'medical_history',
            'laboratory_findings', 'urine_tests', 'additional_studies',
            'physical_examination', 'abnormal_findings', 'assessments',
            'certifications'
        ]
        
    def execute_query(self, query: str, params: tuple = None) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute a SQL query and return results."""
        logger.debug(f"Executing query: {query}")
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
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
        """Get schema information for a specific table."""
        if table_name not in self.expected_tables:
            raise ValueError(f"Table '{table_name}' is not a valid NAVMED table")
        
        try:
            schema_query = f"PRAGMA table_info({table_name})"
            columns = self.execute_query(schema_query)
            
            fk_query = f"PRAGMA foreign_key_list({table_name})"
            foreign_keys = self.execute_query(fk_query)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys,
                "description": self._get_table_description(table_name)
            }
        except Exception as e:
            raise Exception(f"Error getting schema for {table_name}: {str(e)}")

    def create_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the specified table."""
        try:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            result = self.execute_query(query, tuple(data.values()))
            
            return {
                "success": True,
                "inserted_id": result["last_insert_id"],
                "affected_rows": result["affected_rows"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_records(self, table_name: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve records from the specified table with optional filtering."""
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
            
            return self.execute_query(base_query, tuple(params) if params else None)
            
        except Exception as e:
            raise Exception(f"Error retrieving data from {table_name}: {str(e)}")

    def get_examination_with_relations(self, exam_id: int) -> Dict[str, Any]:
        """Get complete examination with all related records."""
        try:
            # Get main examination record
            exam_query = "SELECT * FROM examinations WHERE exam_id = ?"
            examination = self.execute_query(exam_query, (exam_id,))
            
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
                records = self.execute_query(query, (exam_id,))
                result[table] = records
            
            return result
            
        except Exception as e:
            return {"error": f"Error retrieving complete examination: {str(e)}"}

    def get_examination_summary(self, exam_id: int = None, patient_ssn: str = None) -> Dict[str, Any]:
        """Get examination summary with facility and assessment information."""
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
            
            results = self.execute_query(base_query, params)
            return {"examinations": results}
            
        except Exception as e:
            return {"error": f"Error retrieving examination summary: {str(e)}"}

    def _get_table_description(self, table_name: str) -> str:
        """Get description of table based on NAVMED 6470/13 structure."""
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