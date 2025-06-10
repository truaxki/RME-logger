# Radiation Medical Exam MCP Server

A Model Context Protocol (MCP) server designed to create a structured logging system for radiation medical examinations (6470/13 exams) used to monitor radiation workers in the Navy for signs and symptoms of cancer and to clear them for work around ionizing radiation.

**⚠️ IMPORTANT: This is a DEMO server and is NOT HIPAA compliant. DO NOT use this in actual medical practice or with real patient data.**

## Purpose

This MCP server provides tools for logging and managing radiation medical exam data, including:
- Structured data entry for 13 exam fields
- Note-taking capabilities for medical observations
- PDF documentation processing and search
- Summary generation for exam documentation
- Resource management for tracking exam records

## Features

### 📝 Note Management
- Create and store medical examination notes
- Structured data entry with validation
- Real-time resource updates

### 📄 PDF Documentation Integration
- **Automatic PDF Processing**: Extracts text content from radiation health documentation
- **Chapter-Specific Access**: Direct access to specific chapters (e.g., Chapter 2 procedures)
- **Full-Text Search**: Search through PDF content for specific terms, procedures, or regulations
- **Official Reference Material**: Includes Navy Radiation Health Protection Manual (NAVMED P-5055)

### 🔍 Advanced Search Capabilities
- Search across all PDF documentation
- Context-aware results with surrounding text
- Support for medical terminology and procedure names

## Components

### Resources
- **Note Resources**: Custom `note://` URI scheme for accessing individual exam notes
- **PDF Documents**: Full document access via `pdf://document/{filename}` URIs
- **Chapter Access**: Specific chapter content via `pdf://chapter/{filename}/{chapter_number}` URIs
- Each resource includes name, description, and content in text/plain format

### Prompts
- **summarize-notes**: Creates summaries of all stored exam notes
  - Optional "style" argument (brief/detailed) to control summary depth
  - Combines all current notes into a comprehensive exam summary
- **explain-procedure**: Explains radiation medical exam procedures from official documentation
  - Required "procedure" argument to specify which procedure to explain
  - References official Navy documentation for authoritative guidance

### Tools
- **add-note**: Adds new exam notes to the server
  - Required arguments: "name" and "content" (both strings)
  - Updates server state and notifies clients of resource changes
- **search-documentation**: Search through PDF documentation for specific terms
  - Required argument: "search_term" (string) - term to search for
  - Optional argument: "document" (string) - specific document to search
  - Returns matching content with context

## Documentation Integration

The server automatically processes PDF documents stored in `src/radiation_medical_exam/utils/instructions/`:

- **NAVMED P-5055**: Navy Radiation Health Protection Manual
- **Chapter 2**: Medical Examinations (specifically accessible)
- **Full-text search**: Across all available documentation
- **Contextual results**: Search results include surrounding text for better understanding

### Supported PDF Features
- Multi-page document processing
- Chapter extraction and parsing
- Full-text search with context
- Caching for improved performance

## Configuration

### Claude Desktop Setup

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`  
**MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "radiation-medical-exam": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\ktrua\\source\\repos\\radiation-medical-exam",
        "run",
        "radiation-medical-exam"
      ]
    }
  }
}
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd radiation-medical-exam
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Add PDF documentation** (optional):
   - Place PDF files in `src/radiation_medical_exam/utils/instructions/`
   - Supported formats: PDF files with text content
   - Server will automatically detect and process new PDFs

4. **Configure Claude Desktop** using the configuration above

5. **Restart Claude Desktop** to load the server

## Dependencies

- **Python 3.13+**
- **mcp>=1.9.3**: Model Context Protocol SDK
- **pypdf>=4.0.0**: PDF processing and text extraction
- **aiofiles>=23.0.0**: Asynchronous file operations

## Usage Examples

### Basic Note Operations
```
"Add a note about patient examination findings"
"Summarize all current exam notes"
```

### Documentation Search
```
"Search the documentation for 'dose limits'"
"What does Chapter 2 say about medical examinations?"
"Find information about radiation safety protocols"
```

### Procedure Explanations
```
"Explain the radiation medical examination procedure"
"What are the requirements for radiation worker medical qualifications?"
```

## File Structure

```
radiation-medical-exam/
├── src/
│   └── radiation_medical_exam/
│       ├── server.py                 # Main MCP server implementation
│       ├── utils/
│       │   ├── pdf_processor.py      # PDF processing utilities
│       │   └── instructions/         # PDF documentation storage
│       │       └── *.pdf            # Radiation health documentation
│       └── __init__.py
├── pyproject.toml                    # Project configuration
└── README.md                         # This file
```

## Disclaimer

This software is provided for demonstration and educational purposes only. It is not intended for use in actual medical practice and does not comply with HIPAA or other medical data protection regulations. Always consult with qualified medical professionals and use certified, compliant systems for actual radiation medical examinations.

## Contributing

This is a demonstration project. For production medical applications, ensure compliance with:
- HIPAA regulations
- Medical device software standards
- Institutional review board requirements
- Navy medical documentation standards
