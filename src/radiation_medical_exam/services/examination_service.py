"""
Examination service for NAVMED 6470/13 radiation medical examinations.

This module provides high-level business logic for managing radiation medical
examinations, combining repository operations with validation.
"""

from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from ..database.navmed_repository import NavmedRepository
from .validation_service import ValidationService

logger = logging.getLogger(__name__)

class ExaminationService:
    """
    Service for managing NAVMED 6470/13 radiation medical examinations.
    
    Provides high-level operations for creating, retrieving, and managing
    examination data with proper validation and business logic.
    """
    
    def __init__(self, db_path: Path):
        """Initialize service with repository and validation."""
        self.repository = NavmedRepository(db_path)
        self.validator = ValidationService()
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema with validation rules."""
        try:
            schema = self.repository.get_table_schema(table_name)
            validation_rules = self.validator.get_validation_rules(table_name)
            schema['validation_rules'] = validation_rules
            return schema
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            raise
    
    def create_examination_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new examination record with validation.
        
        Args:
            table_name: Name of the table to insert into
            data: Record data to insert
            
        Returns:
            Dict with operation results
        """
        try:
            # Validate data first
            validation_result = self.validator.validate_examination_data(table_name, data)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "errors": validation_result["errors"]
                }
            
            # Create record in repository
            result = self.repository.create_record(table_name, data)
            
            if result["success"]:
                logger.info(f"Created record in {table_name} with ID {result['inserted_id']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating record in {table_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_examination_records(self, table_name: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get examination records with optional filtering."""
        try:
            return self.repository.get_records(table_name, filters, limit)
        except Exception as e:
            logger.error(f"Error retrieving records from {table_name}: {e}")
            raise
    
    def get_complete_examination(self, exam_id: int) -> Dict[str, Any]:
        """Get complete examination with all related records."""
        try:
            return self.repository.get_examination_with_relations(exam_id)
        except Exception as e:
            logger.error(f"Error retrieving complete examination {exam_id}: {e}")
            return {"error": str(e)}
    
    def create_complete_examination(self, examination_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete examination with all related sections.
        
        Args:
            examination_data: Complete examination data with all sections
            
        Returns:
            Dict with creation results
        """
        try:
            # Validate main examination section
            if 'examination' not in examination_data:
                return {"success": False, "error": "Missing examination data"}
            
            # Create main examination record
            exam_result = self.create_examination_record('examinations', examination_data['examination'])
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
                    
                    section_result = self.create_examination_record(section, section_data)
                    if section_result["success"]:
                        created_records[section] = 1
                    else:
                        logger.warning(f"Failed to create {section}: {section_result}")
            
            logger.info(f"Created complete examination with ID {exam_id}")
            return {
                "success": True,
                "exam_id": exam_id,
                "created_records": created_records
            }
            
        except Exception as e:
            logger.error(f"Error creating complete examination: {e}")
            return {"success": False, "error": str(e)}
    
    def get_examination_summary(self, exam_id: int = None, patient_ssn: str = None) -> Dict[str, Any]:
        """Get examination summary for reporting."""
        try:
            return self.repository.get_examination_summary(exam_id=exam_id, patient_ssn=patient_ssn)
        except Exception as e:
            logger.error(f"Error retrieving examination summary: {e}")
            return {"error": str(e)}
    
    def validate_examination_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate examination data without creating record."""
        return self.validator.validate_examination_data(table_name, data)
    
    def get_patient_examinations(self, patient_ssn: str) -> Dict[str, Any]:
        """Get all examinations for a specific patient."""
        try:
            # Get examination summaries for patient
            summary_result = self.get_examination_summary(patient_ssn=patient_ssn)
            
            if "error" in summary_result:
                return summary_result
            
            examinations = summary_result.get("examinations", [])
            
            # Enhance with complete examination data if requested
            enhanced_examinations = []
            for exam in examinations:
                exam_id = exam.get("exam_id")
                if exam_id:
                    complete_exam = self.get_complete_examination(exam_id)
                    if "error" not in complete_exam:
                        enhanced_examinations.append({
                            "summary": exam,
                            "complete_data": complete_exam
                        })
            
            return {
                "patient_ssn": patient_ssn,
                "examination_count": len(examinations),
                "examinations": enhanced_examinations
            }
            
        except Exception as e:
            logger.error(f"Error retrieving patient examinations for {patient_ssn}: {e}")
            return {"error": str(e)}
    
    def search_examinations(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search examinations based on various criteria.
        
        Args:
            search_criteria: Dictionary with search parameters
            
        Returns:
            List of matching examination records
        """
        try:
            # Build filters based on search criteria
            filters = {}
            
            if 'exam_type' in search_criteria:
                filters['exam_type'] = search_criteria['exam_type']
            
            if 'patient_last_name' in search_criteria:
                filters['patient_last_name'] = search_criteria['patient_last_name']
            
            if 'command_unit' in search_criteria:
                filters['command_unit'] = search_criteria['command_unit']
            
            if 'date_from' in search_criteria or 'date_to' in search_criteria:
                # For date range searches, we'll need custom query logic
                logger.warning("Date range searches not yet implemented")
            
            limit = search_criteria.get('limit', 50)
            
            return self.get_examination_records('examinations', filters, limit)
            
        except Exception as e:
            logger.error(f"Error searching examinations: {e}")
            raise
    
    def get_examination_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about examinations in the database."""
        try:
            # Get total examination count
            all_exams = self.get_examination_records('examinations', limit=1000)
            total_count = len(all_exams)
            
            # Count by exam type
            exam_type_counts = {}
            for exam in all_exams:
                exam_type = exam.get('exam_type', 'Unknown')
                exam_type_counts[exam_type] = exam_type_counts.get(exam_type, 0) + 1
            
            # Count by year
            year_counts = {}
            for exam in all_exams:
                exam_date = exam.get('exam_date', '')
                if exam_date:
                    year = exam_date[:4] if len(exam_date) >= 4 else 'Unknown'
                    year_counts[year] = year_counts.get(year, 0) + 1
            
            return {
                "total_examinations": total_count,
                "by_exam_type": exam_type_counts,
                "by_year": year_counts,
                "database_tables": len(self.repository.expected_tables)
            }
            
        except Exception as e:
            logger.error(f"Error getting examination statistics: {e}")
            return {"error": str(e)}