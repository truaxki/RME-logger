"""
Refactored NAVMED 6470/13 Radiation Medical Examination MCP Server.

This server provides clean, organized access to radiation medical examination data
with proper separation of concerns using handlers and services.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from .utils.pdf_processor import PDFProcessor
from .handlers.tool_handlers import ToolHandlers
from .handlers.resource_handlers import ResourceHandlers
from .handlers.prompt_handlers import PromptHandlers

# Store notes as a simple key-value dict to demonstrate state management
notes: Dict[str, str] = {}

# Initialize PDF processor
INSTRUCTIONS_PATH = Path(__file__).parent / "utils" / "instructions"
pdf_processor = PDFProcessor(str(INSTRUCTIONS_PATH))

# Database path
DB_PATH = Path(__file__).parent / "data" / "navmed_radiation_exam.db"

server = Server("radiation-medical-exam")

# Initialize handlers
tool_handlers = ToolHandlers(DB_PATH, pdf_processor, notes)
resource_handlers = ResourceHandlers(notes, pdf_processor)
prompt_handlers = PromptHandlers(notes)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources including notes, PDF documents, and database schemas."""
    return await resource_handlers.list_resources()

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource's content by its URI."""
    return await resource_handlers.read_resource(uri)

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available prompts."""
    return await prompt_handlers.list_prompts()

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """Generate a prompt by combining arguments with server state."""
    return await prompt_handlers.get_prompt(name, arguments)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for the radiation medical exam system."""
    return [
        # Note management
        types.Tool(
            name="add-note",
            description="Add a note to the system",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the note"},
                    "content": {"type": "string", "description": "Content of the note"},
                },
                "required": ["name", "content"],
            },
        ),
        
        # Documentation search
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
        
        # Database management
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
        
        # Schema operations
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
        
        # Data operations
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
        
        # Complete examination operations
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
        
        # Summary and reporting
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
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle all tool calls by delegating to appropriate handlers."""
    
    # Route to appropriate handler based on tool name
    handler_map = {
        "add-note": tool_handlers.handle_add_note,
        "search-documentation": tool_handlers.handle_search_documentation,
        "initialize-database": tool_handlers.handle_initialize_database,
        "get-table-schema": tool_handlers.handle_get_table_schema,
        "add-exam-data": tool_handlers.handle_add_exam_data,
        "get-exam-data": tool_handlers.handle_get_exam_data,
        "get-complete-exam": tool_handlers.handle_get_complete_exam,
        "create-complete-exam": tool_handlers.handle_create_complete_exam,
        "get-exam-summary": tool_handlers.handle_get_exam_summary,
    }
    
    if name not in handler_map:
        raise ValueError(f"Unknown tool: {name}")
    
    # Call the appropriate handler
    return await handler_map[name](arguments or {})

async def main():
    """Run the refactored server using stdin/stdout streams."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="radiation-medical-exam",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 