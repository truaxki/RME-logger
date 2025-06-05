import asyncio
import os
import json
import sys
import sqlite3
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from .utils.pdf_processor import PDFProcessor
from .utils.navmed_database import NavmedDatabase

# Import the database creation function from the init script
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
from init_navmed_database import create_database, verify_database

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

# Initialize PDF processor
INSTRUCTIONS_PATH = os.path.join(os.path.dirname(__file__), "utils", "instructions")
pdf_processor = PDFProcessor(INSTRUCTIONS_PATH)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "navmed_radiation_exam.db")

# Initialize NAVMED database interface
navmed_db = NavmedDatabase(DB_PATH)

server = Server("radiation-medical-exam")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available resources including notes, PDF documents, and database schemas.
    Each resource is exposed with a custom URI scheme.
    """
    resources = []
    
    # Add note resources
    resources.extend([
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ])
    
    # Add PDF document resources
    available_pdfs = pdf_processor.get_available_pdfs()
    for pdf_file in available_pdfs:
        # Full document
        resources.append(
            types.Resource(
                uri=AnyUrl(f"pdf://document/{pdf_file}"),
                name=f"Document: {pdf_file}",
                description=f"Complete content of {pdf_file}",
                mimeType="text/plain",
            )
        )
        
        # Chapter 2 specifically (since you mentioned it)
        if "5055" in pdf_file:  # Your specific document
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"pdf://chapter/{pdf_file}/2"),
                    name=f"Chapter 2: {pdf_file}",
                    description="Chapter 2 - Radiation Medical Exam Instructions and Procedures",
                    mimeType="text/plain",
                )
            )
    

    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific resource's content by its URI.
    Supports notes, PDF documents, and database schemas.
    """
    if uri.scheme == "note":
        name = uri.path
        if name is not None:
            name = name.lstrip("/")
            if name in notes:
                return notes[name]
        raise ValueError(f"Note not found: {name}")
    
    elif uri.scheme == "pdf":
        path_parts = uri.path.lstrip("/").split("/")
        
        if len(path_parts) >= 2:
            resource_type = path_parts[0]  # "document" or "chapter"
            pdf_filename = path_parts[1]
            
            if resource_type == "document":
                # Return full document
                return await pdf_processor.extract_text_from_pdf(pdf_filename)
            
            elif resource_type == "chapter" and len(path_parts) >= 3:
                # Return specific chapter
                chapter_num = int(path_parts[2])
                return await pdf_processor.extract_chapter(pdf_filename, chapter_num)
        
        raise ValueError(f"Invalid PDF resource path: {uri.path}")
    
    raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        ),
        types.Prompt(
            name="explain-procedure",
            description="Explain a radiation medical exam procedure from the documentation",
            arguments=[
                types.PromptArgument(
                    name="procedure",
                    description="Name of the procedure to explain",
                    required=True,
                )
            ],
        ),
        types.Prompt(
            name="create-exam-template",
            description="Create a template for a radiation medical examination",
            arguments=[
                types.PromptArgument(
                    name="exam_type",
                    description="Type of examination (PE, RE, SE, TE)",
                    required=True,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes all current notes and can be customized via arguments.
    """
    if name == "summarize-notes":
        style = (arguments or {}).get("style", "brief")
        detail_prompt = " Give extensive details." if style == "detailed" else ""

        return types.GetPromptResult(
            description="Summarize the current notes",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                        + "\n".join(
                            f"- {name}: {content}"
                            for name, content in notes.items()
                        ),
                    ),
                )
            ],
        )
    
    elif name == "explain-procedure":
        procedure = (arguments or {}).get("procedure", "")
        if not procedure:
            raise ValueError("Procedure name is required")

        return types.GetPromptResult(
            description=f"Explain the {procedure} radiation medical exam procedure",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Based on the radiation medical exam documentation available as resources, please explain the {procedure} procedure in detail. Include any relevant safety protocols, equipment requirements, and step-by-step instructions.",
                    ),
                )
            ],
        )
    
    elif name == "create-exam-template":
        exam_type = (arguments or {}).get("exam_type", "")
        if not exam_type:
            raise ValueError("Exam type is required")

        return types.GetPromptResult(
            description=f"Create a template for {exam_type} radiation medical examination",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Create a template for a {exam_type} (Pre-employment/Reexamination/Situational/Termination) radiation medical examination. Include all required sections from the NAVMED 6470/13 form and reference the database schema resources for proper field formats and validation requirements.",
                    ),
                )
            ],
        )
    
    raise ValueError(f"Unknown prompt: {name}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="add-note",
            description="Add a new note",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        ),
        types.Tool(
            name="search-documentation",
            description="Search through the PDF documentation for specific terms",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Term to search for in documentation"},
                    "document": {"type": "string", "description": "Specific document to search (optional)"},
                },
                "required": ["search_term"],
            },
        ),
        types.Tool(
            name="initialize-database",
            description="Create and initialize the NAVMED 6470/13 database with tables and sample data. Checks if database exists first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Overwrite existing database if it exists (default: false)",
                        "default": False
                    },
                    "include_sample_data": {
                        "type": "boolean", 
                        "description": "Include sample examination data for testing (default: true)",
                        "default": True
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get-table-schema",
            description="Get the schema information for a specific NAVMED table including columns, foreign keys, and descriptions",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the NAVMED table",
                        "enum": ["examinations", "examining_facilities", "medical_history", "laboratory_findings", "urine_tests", "additional_studies", "physical_examination", "abnormal_findings", "assessments", "certifications"]
                    }
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="add-exam-data",
            description="Add data to any NAVMED examination table with validation based on NAVMED 6470/13 requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the NAVMED table to insert data into",
                        "enum": ["examinations", "examining_facilities", "medical_history", "laboratory_findings", "urine_tests", "additional_studies", "physical_examination", "abnormal_findings", "assessments", "certifications"]
                    },
                    "data": {
                        "type": "object",
                        "description": "Dictionary of column names and values to insert"
                    }
                },
                "required": ["table_name", "data"],
            },
        ),
        types.Tool(
            name="get-exam-data", 
            description="Retrieve data from any NAVMED examination table with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the NAVMED table to query",
                        "enum": ["examinations", "examining_facilities", "medical_history", "laboratory_findings", "urine_tests", "additional_studies", "physical_examination", "abnormal_findings", "assessments", "certifications"]
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional dictionary of column names and values to filter by"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="get-complete-exam",
            description="Get complete examination data with all related records from all tables",
            inputSchema={
                "type": "object",
                "properties": {
                    "exam_id": {
                        "type": "integer",
                        "description": "Examination ID to retrieve complete data for"
                    }
                },
                "required": ["exam_id"],
            },
        ),
        types.Tool(
            name="create-complete-exam",
            description="Create a complete examination with all related data sections following NAVMED 6470/13 structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "examination_data": {
                        "type": "object", 
                        "description": "Complete examination data with sections for examination, medical_history, laboratory_findings, etc.",
                        "properties": {
                            "examination": {
                                "type": "object",
                                "description": "Main examination record data"
                            },
                            "medical_history": {
                                "type": "object",
                                "description": "Medical history data (blocks 3-10)"
                            },
                            "laboratory_findings": {
                                "type": "object", 
                                "description": "Laboratory test results (block 11)"
                            },
                            "urine_tests": {
                                "type": "object",
                                "description": "Urine test results (block 12)"
                            },
                            "additional_studies": {
                                "type": "object",
                                "description": "Additional medical studies (block 13)"
                            },
                            "physical_examination": {
                                "type": "object",
                                "description": "Physical examination findings (blocks 15-19)"
                            },
                            "abnormal_findings": {
                                "type": "object",
                                "description": "Summary of abnormal findings (block 14)"
                            },
                            "assessments": {
                                "type": "object",
                                "description": "Medical assessments (blocks 20a, 20b)"
                            },
                            "certifications": {
                                "type": "object",
                                "description": "Signatures and certifications (blocks 21-23)"
                            }
                        },
                        "required": ["examination"]
                    }
                },
                "required": ["examination_data"],
            },
        ),
        types.Tool(
            name="get-exam-summary",
            description="Get a summary of examination(s) for reporting purposes with facility and assessment information",
            inputSchema={
                "type": "object",
                "properties": {
                    "exam_id": {
                        "type": "integer",
                        "description": "Specific examination ID to get summary for"
                    },
                    "patient_ssn": {
                        "type": "string",
                        "description": "Patient SSN to get all examinations for (format: XXX-XX-XXXX)"
                    }
                },
                "required": [],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if name == "add-note":
        if not arguments:
            raise ValueError("Missing arguments")

        note_name = arguments.get("name")
        content = arguments.get("content")

        if not note_name or not content:
            raise ValueError("Missing name or content")

        # Update server state
        notes[note_name] = content

        # Notify clients that resources have changed
        await server.request_context.session.send_resource_list_changed()

        return [
            types.TextContent(
                type="text",
                text=f"Added note '{note_name}' with content: {content}",
            )
        ]
    
    elif name == "search-documentation":
        if not arguments:
            raise ValueError("Missing arguments")

        search_term = arguments.get("search_term")
        if not search_term:
            raise ValueError("Missing search term")

        document = arguments.get("document")
        results = []
        
        # Search through available PDFs
        available_pdfs = pdf_processor.get_available_pdfs()
        pdfs_to_search = [document] if document and document in available_pdfs else available_pdfs
        
        for pdf_file in pdfs_to_search:
            try:
                content = await pdf_processor.extract_text_from_pdf(pdf_file)
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
    
    elif name == "initialize-database":
        force = arguments.get("force", False) if arguments else False
        include_sample_data = arguments.get("include_sample_data", True) if arguments else True
        
        try:
            db_path = Path(DB_PATH)
            
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
            success = create_database(db_path, force=force, include_sample_data=include_sample_data)
            
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
    
    elif name == "get-table-schema":
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        if not table_name:
            raise ValueError("Missing table_name")

        try:
            schema = navmed_db.get_table_schema(table_name)
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
                          ]) if schema['foreign_keys'] else "\n\n🔗 **Foreign Keys:** None")
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ Error getting schema for {table_name}: {str(e)}"
                )
            ]
    
    elif name == "add-exam-data":
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        data = arguments.get("data")
        
        if not table_name or not data:
            raise ValueError("Missing table_name or data")

        try:
            result = navmed_db.add_examination_data(table_name, data)
            
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
    
    elif name == "get-exam-data":
        if not arguments:
            raise ValueError("Missing arguments")

        table_name = arguments.get("table_name")
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 10)
        
        if not table_name:
            raise ValueError("Missing table_name")

        try:
            results = navmed_db.get_examination_data(table_name, filters, limit)
            
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
    
    elif name == "get-complete-exam":
        if not arguments:
            raise ValueError("Missing arguments")

        exam_id = arguments.get("exam_id")
        if not exam_id:
            raise ValueError("Missing exam_id")

        try:
            result = navmed_db.get_complete_examination(exam_id)
            
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
    
    elif name == "create-complete-exam":
        if not arguments:
            raise ValueError("Missing arguments")

        examination_data = arguments.get("examination_data")
        if not examination_data:
            raise ValueError("Missing examination_data")

        try:
            result = navmed_db.create_complete_examination(examination_data)
            
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
    
    elif name == "get-exam-summary":
        if not arguments:
            arguments = {}

        exam_id = arguments.get("exam_id")
        patient_ssn = arguments.get("patient_ssn")
        
        if not exam_id and not patient_ssn:
            raise ValueError("Must provide either exam_id or patient_ssn")

        try:
            result = navmed_db.get_examination_summary(exam_id=exam_id, patient_ssn=patient_ssn)
            
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
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="radiation-medical-exam",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
