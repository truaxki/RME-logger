"""
Tool handlers for NAVMED 6470/13 MCP server.

This module contains all the tool handling logic extracted from the main server
for better organization and maintainability.
"""

from typing import Dict, Any, List
import sqlite3
from pathlib import Path
import logging

from mcp import types
from ..services.examination_service import ExaminationService
from ..database.init_database import initialize_database, verify_database

logger = logging.getLogger(__name__)

class ToolHandlers:
    """Handles all MCP tool operations for the NAVMED server."""
    
    def __init__(self, db_path: Path, pdf_processor, notes: Dict[str, str]):
        """Initialize with required dependencies."""
        self.db_path = db_path
        self.pdf_processor = pdf_processor
        self.notes = notes
        self.examination_service = ExaminationService(db_path)
    
    async def handle_add_note(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle add-note tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        note_name = arguments.get("name")
        content = arguments.get("content")

        if not note_name or not content:
            raise ValueError("Missing name or content")

        # Update server state
        self.notes[note_name] = content

        return [
            types.TextContent(
                type="text",
                text=f"Added note '{note_name}' with content: {content}",
            )
        ]
    
    async def handle_search_documentation(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle search-documentation tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        search_term = arguments.get("search_term")
        if not search_term:
            raise ValueError("Missing search term")

        document = arguments.get("document")
        results = []
        
        # Search through available PDFs
        available_pdfs = self.pdf_processor.get_available_pdfs()
        pdfs_to_search = [document] if document and document in available_pdfs else available_pdfs
        
        for pdf_file in pdfs_to_search:
            try:
                content = await self.pdf_processor.extract_text_from_pdf(pdf_file)
                lines = content.split('\n')
                matching_lines = []
                
                for i, line in enumerate(lines):
                    if search_term.lower() in line.lower():
                        # Include context (line before and after)
                        context_start = max(0, i-1)
                        context_end = min(len(lines), i+2)
                        context = lines[context_start:context_end]
                        matching_lines.extend(context)
                        matching_lines.append("---")
                
                if matching_lines:
                    results.append(f"**Found in {pdf_file}:**\n" + "\n".join(matching_lines))
            
            except Exception as e:
                results.append(f"Error searching {pdf_file}: {str(e)}")
        
        if not results:
            results.append(f"No matches found for '{search_term}' in available documentation.")
        
        return [
            types.TextContent(
                type="text",
                text="\n\n".join(results),
            )
        ]
    
    async def handle_initialize_database(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle initialize-database tool."""
        force = arguments.get("force", False) if arguments else False
        include_sample_data = arguments.get("include_sample_data", True) if arguments else True
        
        try:
            db_path = Path(self.db_path)
            
            # Check if database already exists and has content
            if db_path.exists() and not force:
                # Check if database has tables
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        existing_tables = [row[0] for row in cursor.fetchall()]
                        navmed_tables = [t for t in existing_tables if t != 'sqlite_sequence']
                        
                        if navmed_tables:
                            return [
                                types.TextContent(
                                    type="text",
                                    text=f"⚠️ Database already exists at {db_path} with {len(navmed_tables)} tables:\n"
                                         f"📋 Tables: {', '.join(navmed_tables)}\n\n"
                                         f"🔧 Use force=true to overwrite existing database\n"
                                         f"✅ Or use the verification tool to check database integrity"
                                )
                            ]
                except Exception:
                    # If we can't read the database, treat it as corrupted and allow recreation
                    pass
            
            # Create the database
            success = initialize_database(db_path, force=force, include_sample_data=include_sample_data)
            
            if success:
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ Database successfully created at {db_path}\n"
                             f"📊 Force overwrite: {'Yes' if force else 'No'}\n"
                             f"📝 Sample data included: {'Yes' if include_sample_data else 'No'}\n"
                             f"🏥 Ready for NAVMED 6470/13 examination data!"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ Failed to create database at {db_path}.\n"
                             f"💡 Check the logs for more details or try with force=true"
                    )
                ]
        
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error creating database: {str(e)}"
                )
            ]
    
    async def handle_get_table_schema(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle get-table-schema tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        if not table_name:
            raise ValueError("Missing table_name")

        try:
            schema = self.examination_service.get_table_schema(table_name)
            return [
                types.TextContent(
                    type="text",
                    text=f"📊 **Schema for {table_name}**\n\n"
                         f"📋 **Description:** {schema['description']}\n\n"
                         f"🏗️ **Columns ({len(schema['columns'])}):**\n" + 
                         "\n".join([
                             f"  • **{col['name']}** ({col['type']}) - "
                             f"{'NOT NULL' if col['notnull'] else 'NULL'} - "
                             f"{'PRIMARY KEY' if col['pk'] else ''} - "
                             f"Default: {col['dflt_value'] or 'None'}"
                             for col in schema['columns']
                         ]) +
                         (f"\n\n🔗 **Foreign Keys ({len(schema['foreign_keys'])}):**\n" + 
                          "\n".join([
                              f"  • {fk['from']} → {fk['table']}.{fk['to']}"
                              for fk in schema['foreign_keys']
                          ]) if schema['foreign_keys'] else "\n\n🔗 **Foreign Keys:** None") +
                         (f"\n\n✅ **Validation Rules:**\n" + 
                          "\n".join([f"  • **{k}:** {v}" for k, v in schema.get('validation_rules', {}).items()])
                          if schema.get('validation_rules') else "")
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error getting schema for {table_name}: {str(e)}"
                )
            ]
    
    async def handle_add_exam_data(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle add-exam-data tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        data = arguments.get("data")
        
        if not table_name or not data:
            raise ValueError("Missing table_name or data")

        try:
            result = self.examination_service.create_examination_record(table_name, data)
            
            if result["success"]:
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ **Data added successfully to {table_name}**\n\n"
                             f"🆔 **Record ID:** {result['inserted_id']}\n"
                             f"📝 **Rows affected:** {result['affected_rows']}\n"
                             f"🏥 **Table:** {table_name}"
                    )
                ]
            else:
                error_text = "❌ **Validation failed**\n\n" + "\n".join([f"• {error}" for error in result.get("errors", [])])
                if result.get("error"):
                    error_text += f"\n\n**Error:** {result['error']}"
                
                return [
                    types.TextContent(
                        type="text",
                        text=error_text
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error adding data to {table_name}: {str(e)}"
                )
            ]
    
    async def handle_get_exam_data(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle get-exam-data tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 10)
        
        if not table_name:
            raise ValueError("Missing table_name")

        try:
            results = self.examination_service.get_examination_records(table_name, filters, limit)
            
            if results:
                result_text = f"📊 **Found {len(results)} records in {table_name}**\n\n"
                
                for i, record in enumerate(results, 1):
                    result_text += f"**Record {i}:**\n"
                    for key, value in record.items():
                        result_text += f"  • **{key}:** {value}\n"
                    result_text += "\n"
                
                return [
                    types.TextContent(
                        type="text",
                        text=result_text
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"📭 No records found in {table_name}" + 
                              (f" matching filters: {filters}" if filters else "")
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error retrieving data from {table_name}: {str(e)}"
                )
            ]
    
    async def handle_get_complete_exam(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle get-complete-exam tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        exam_id = arguments.get("exam_id")
        if not exam_id:
            raise ValueError("Missing exam_id")

        try:
            result = self.examination_service.get_complete_examination(exam_id)
            
            if "error" in result:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ {result['error']}"
                    )
                ]
            
            # Format the complete examination data
            result_text = f"🏥 **Complete Examination - ID: {exam_id}**\n\n"
            
            # Main examination info
            exam = result["examination"]
            result_text += f"**📋 Main Examination:**\n"
            for key, value in exam.items():
                result_text += f"  • **{key}:** {value}\n"
            result_text += "\n"
            
            # Related records
            sections = ["medical_history", "laboratory_findings", "urine_tests", "additional_studies", 
                       "physical_examination", "abnormal_findings", "assessments", "certifications"]
            
            for section in sections:
                if section in result and result[section]:
                    result_text += f"**📝 {section.replace('_', ' ').title()}:**\n"
                    for record in result[section]:
                        for key, value in record.items():
                            if key != 'exam_id':  # Skip exam_id as it's redundant
                                result_text += f"  • **{key}:** {value}\n"
                    result_text += "\n"
            
            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error retrieving complete examination: {str(e)}"
                )
            ]
    
    async def handle_create_complete_exam(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle create-complete-exam tool."""
        if not arguments:
            raise ValueError("Missing arguments")

        examination_data = arguments.get("examination_data")
        if not examination_data:
            raise ValueError("Missing examination_data")

        try:
            result = self.examination_service.create_complete_examination(examination_data)
            
            if result["success"]:
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ **Complete examination created successfully**\n\n"
                             f"🆔 **Examination ID:** {result['exam_id']}\n"
                             f"📊 **Records Created:**\n" + 
                             "\n".join([f"  • **{table}:** {count} record(s)" 
                                       for table, count in result['created_records'].items()]) +
                             f"\n\n🏥 **Ready for medical review and certification**"
                    )
                ]
            else:
                error_text = "❌ **Failed to create complete examination**\n\n"
                if result.get("errors"):
                    error_text += "\n".join([f"• {error}" for error in result["errors"]])
                if result.get("error"):
                    error_text += f"**Error:** {result['error']}"
                
                return [
                    types.TextContent(
                        type="text",
                        text=error_text
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error creating complete examination: {str(e)}"
                )
            ]
    
    async def handle_get_exam_summary(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle get-exam-summary tool."""
        if not arguments:
            arguments = {}

        exam_id = arguments.get("exam_id")
        patient_ssn = arguments.get("patient_ssn")
        
        if not exam_id and not patient_ssn:
            raise ValueError("Must provide either exam_id or patient_ssn")

        try:
            result = self.examination_service.get_examination_summary(exam_id=exam_id, patient_ssn=patient_ssn)
            
            if "error" in result:
                return [
                    types.TextContent(
                        type="text",
                        text=f"❌ {result['error']}"
                    )
                ]
            
            examinations = result["examinations"]
            if not examinations:
                search_term = f"ID {exam_id}" if exam_id else f"SSN {patient_ssn}"
                return [
                    types.TextContent(
                        type="text",
                        text=f"📭 No examinations found for {search_term}"
                    )
                ]
            
            result_text = f"📊 **Examination Summary ({len(examinations)} record(s))**\n\n"
            
            for exam in examinations:
                result_text += f"**🏥 Examination ID: {exam['exam_id']}**\n"
                result_text += f"  • **Patient:** {exam.get('patient_name', 'N/A')} (SSN: {exam.get('patient_ssn', 'N/A')})\n"
                result_text += f"  • **Date:** {exam.get('exam_date', 'N/A')}\n"
                result_text += f"  • **Type:** {exam.get('exam_type', 'N/A')}\n"
                result_text += f"  • **Facility:** {exam.get('facility_name', 'N/A')}\n"
                result_text += f"  • **Assessment:** {exam.get('initial_assessment', 'N/A')}\n"
                result_text += f"  • **Completed:** {exam.get('examination_complete_date', 'N/A')}\n"
                result_text += "\n"
            
            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error retrieving examination summary: {str(e)}"
                )
            ] 