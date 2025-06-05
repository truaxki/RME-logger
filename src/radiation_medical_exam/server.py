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
