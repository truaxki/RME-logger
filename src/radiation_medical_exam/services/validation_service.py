"""
Validation service for NAVMED 6470/13 radiation medical examination data.

This module handles all validation logic for medical examination data
following the specific requirements and business rules of NAVMED 6470/13.
"""

from typing import Dict, List, Any
import re
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for validating NAVMED 6470/13 examination data."""
    
    def __init__(self):
        """Initialize validation service with rules."""
        self.exam_types = ['PE', 'RE', 'SE', 'TE']
        self.status_values = ['NML', 'ABN', 'NE']
        self.assessment_values = ['PQ', 'NPQ']
        self.finding_categories = ['CD', 'NCD']
        self.urine_results = ['Negative', 'Positive', 'Not Performed']
    
    def validate_examination_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate examination data based on table and NAVMED requirements.
        
        Args:
            table_name: Name of the table being validated
            data: Data dictionary to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        try:
            # Table-specific validation
            if table_name == 'examinations':
                errors.extend(self._validate_examination_record(data))
            elif table_name == 'medical_history':
                errors.extend(self._validate_medical_history(data))
            elif table_name == 'laboratory_findings':
                errors.extend(self._validate_laboratory_findings(data))
            elif table_name == 'urine_tests':
                errors.extend(self._validate_urine_tests(data))
            elif table_name == 'physical_examination':
                errors.extend(self._validate_physical_examination(data))
            elif table_name == 'abnormal_findings':
                errors.extend(self._validate_abnormal_findings(data))
            elif table_name == 'assessments':
                errors.extend(self._validate_assessments(data))
            elif table_name == 'certifications':
                errors.extend(self._validate_certifications(data))
            
            # Common field validation for all tables
            errors.extend(self._validate_common_fields(data))
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_examination_record(self, data: Dict[str, Any]) -> List[str]:
        """Validate main examination record."""
        errors = []
        
        # Exam type validation
        if 'exam_type' in data and data['exam_type'] not in self.exam_types:
            errors.append(f"exam_type must be one of: {', '.join(self.exam_types)} (PE=Physical, RE=Re-examination, SE=Special, TE=Termination)")
        
        # SSN validation
        if 'patient_ssn' in data and data['patient_ssn']:
            if not self._validate_ssn_format(data['patient_ssn']):
                errors.append("patient_ssn must be in format XXX-XX-XXXX")
        
        # Required fields for examination
        required_fields = ['exam_type', 'exam_date', 'patient_last_name', 'patient_first_name', 'patient_ssn', 'patient_dob']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field missing: {field}")
        
        return errors
    
    def _validate_medical_history(self, data: Dict[str, Any]) -> List[str]:
        """Validate medical history data (blocks 3-10)."""
        errors = []
        
        # Validate Yes/No fields
        yes_no_fields = [
            'cancer_history', 'radiation_therapy', 'chemotherapy', 
            'radioactive_drugs', 'xray_studies', 'nuclear_medicine', 
            'occupational_exposure'
        ]
        
        for field in yes_no_fields:
            if field in data and data[field] and data[field] not in ['Yes', 'No']:
                errors.append(f"{field} must be 'Yes' or 'No'")
        
        # If cancer history is Yes, details should be provided
        if data.get('cancer_history') == 'Yes' and not data.get('cancer_details'):
            errors.append("cancer_details required when cancer_history is 'Yes'")
        
        return errors
    
    def _validate_laboratory_findings(self, data: Dict[str, Any]) -> List[str]:
        """Validate laboratory findings (block 11)."""
        errors = []
        
        # Hematocrit validation
        if 'hematocrit' in data and data['hematocrit'] is not None:
            hct = data['hematocrit']
            if not isinstance(hct, (int, float)) or hct < 0 or hct > 100:
                errors.append("hematocrit must be a number between 0 and 100")
        
        # WBC count validation
        if 'wbc_count' in data and data['wbc_count'] is not None:
            wbc = data['wbc_count']
            if not isinstance(wbc, int) or wbc < 0 or wbc > 50000:
                errors.append("wbc_count must be a positive integer less than 50,000")
        
        # Differential validation (should add up to 100)
        diff_fields = ['differential_neutrophils', 'differential_lymphocytes', 
                      'differential_monocytes', 'differential_eosinophils', 'differential_basophils']
        
        diff_values = []
        for field in diff_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], int) or data[field] < 0 or data[field] > 100:
                    errors.append(f"{field} must be an integer between 0 and 100")
                else:
                    diff_values.append(data[field])
        
        if len(diff_values) > 1 and sum(diff_values) != 100:
            errors.append("Differential percentages must sum to 100")
        
        return errors
    
    def _validate_urine_tests(self, data: Dict[str, Any]) -> List[str]:
        """Validate urine test results (block 12)."""
        errors = []
        
        if 'dipstick_blood_result' in data and data['dipstick_blood_result']:
            if data['dipstick_blood_result'] not in self.urine_results:
                errors.append(f"dipstick_blood_result must be one of: {', '.join(self.urine_results)}")
        
        return errors
    
    def _validate_physical_examination(self, data: Dict[str, Any]) -> List[str]:
        """Validate physical examination findings (blocks 15-19)."""
        errors = []
        
        # Status field validation
        status_fields = ['thyroid_status', 'breast_status', 'testes_status', 'dre_status', 'skin_status']
        for field in status_fields:
            if field in data and data[field] and data[field] not in self.status_values:
                errors.append(f"{field} must be one of: {', '.join(self.status_values)} (NML=Normal, ABN=Abnormal, NE=Not Examined)")
        
        return errors
    
    def _validate_abnormal_findings(self, data: Dict[str, Any]) -> List[str]:
        """Validate abnormal findings (block 14)."""
        errors = []
        
        if 'finding_category' in data and data['finding_category']:
            if data['finding_category'] not in self.finding_categories:
                errors.append(f"finding_category must be one of: {', '.join(self.finding_categories)} (CD=Considered Disqualifying, NCD=Not Considered Disqualifying)")
        
        return errors
    
    def _validate_assessments(self, data: Dict[str, Any]) -> List[str]:
        """Validate medical assessments (blocks 20a, 20b)."""
        errors = []
        
        assessment_fields = ['initial_assessment', 'reab_final_determination']
        for field in assessment_fields:
            if field in data and data[field] and data[field] not in self.assessment_values:
                errors.append(f"{field} must be one of: {', '.join(self.assessment_values)} (PQ=Physically Qualified, NPQ=Not Physically Qualified)")
        
        return errors
    
    def _validate_certifications(self, data: Dict[str, Any]) -> List[str]:
        """Validate certifications and signatures (blocks 21-23)."""
        errors = []
        
        # Date validation
        date_fields = ['examination_complete_date', 'review_date', 'patient_signature_date']
        for field in date_fields:
            if field in data and data[field]:
                if not self._validate_date_format(data[field]):
                    errors.append(f"{field} must be in YYYY-MM-DD format")
        
        return errors
    
    def _validate_common_fields(self, data: Dict[str, Any]) -> List[str]:
        """Validate common fields across all tables."""
        errors = []
        
        # Validate exam_id if present (must be positive integer)
        if 'exam_id' in data and data['exam_id'] is not None:
            if not isinstance(data['exam_id'], int) or data['exam_id'] <= 0:
                errors.append("exam_id must be a positive integer")
        
        return errors
    
    def _validate_ssn_format(self, ssn: str) -> bool:
        """Validate SSN format (XXX-XX-XXXX)."""
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        return bool(re.match(pattern, ssn))
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, str(date_str)))
    
    def get_validation_rules(self, table_name: str) -> Dict[str, Any]:
        """Get validation rules for a specific table."""
        rules = {
            'examinations': {
                'exam_type': f"One of: {', '.join(self.exam_types)}",
                'patient_ssn': "Format: XXX-XX-XXXX",
                'required_fields': ['exam_type', 'exam_date', 'patient_last_name', 'patient_first_name', 'patient_ssn', 'patient_dob']
            },
            'medical_history': {
                'yes_no_fields': ['cancer_history', 'radiation_therapy', 'chemotherapy', 'radioactive_drugs', 'xray_studies', 'nuclear_medicine', 'occupational_exposure'],
                'conditional_required': {'cancer_details': 'Required if cancer_history is Yes'}
            },
            'laboratory_findings': {
                'hematocrit': "Number between 0-100",
                'wbc_count': "Positive integer < 50,000",
                'differential': "Percentages must sum to 100"
            },
            'physical_examination': {
                'status_fields': f"One of: {', '.join(self.status_values)} (NML=Normal, ABN=Abnormal, NE=Not Examined)"
            },
            'assessments': {
                'assessment_fields': f"One of: {', '.join(self.assessment_values)} (PQ=Physically Qualified, NPQ=Not Physically Qualified)"
            }
        }
        
        return rules.get(table_name, {}) 