"""
Resource handlers for NAVMED 6470/13 MCP server.

This module handles all resource operations including notes and PDF documents.
"""

from typing import Dict, List
import logging

from mcp import types
from pydantic import AnyUrl

logger = logging.getLogger(__name__)

class ResourceHandlers:
    """Handles all MCP resource operations for the NAVMED server."""
    
    def __init__(self, notes: Dict[str, str], pdf_processor):
        """Initialize with required dependencies."""
        self.notes = notes
        self.pdf_processor = pdf_processor
    
    async def list_resources(self) -> List[types.Resource]:
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
            for name in self.notes
        ])
        
        # Add PDF document resources
        available_pdfs = self.pdf_processor.get_available_pdfs()
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
            
            # Chapter 2 specifically (since it's referenced in documentation)
            if "5055" in pdf_file:  # NAVMED specific document
                resources.append(
                    types.Resource(
                        uri=AnyUrl(f"pdf://chapter/{pdf_file}/2"),
                        name=f"Chapter 2: {pdf_file}",
                        description="Chapter 2 - Radiation Medical Exam Instructions and Procedures",
                        mimeType="text/plain",
                    )
                )
        
        return resources
    
    async def read_resource(self, uri: AnyUrl) -> str:
        """
        Read a specific resource's content by its URI.
        Supports notes, PDF documents, and database schemas.
        """
        if uri.scheme == "note":
            name = uri.path
            if name is not None:
                name = name.lstrip("/")
                if name in self.notes:
                    return self.notes[name]
            raise ValueError(f"Note not found: {name}")
        
        elif uri.scheme == "pdf":
            path_parts = uri.path.lstrip("/").split("/")
            
            if len(path_parts) >= 2:
                resource_type = path_parts[0]  # "document" or "chapter"
                pdf_filename = path_parts[1]
                
                if resource_type == "document":
                    # Return full document
                    return await self.pdf_processor.extract_text_from_pdf(pdf_filename)
                
                elif resource_type == "chapter" and len(path_parts) >= 3:
                    # Return specific chapter
                    chapter_num = int(path_parts[2])
                    return await self.pdf_processor.extract_chapter(pdf_filename, chapter_num)
            
            raise ValueError(f"Invalid PDF resource path: {uri.path}")
        
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}") 