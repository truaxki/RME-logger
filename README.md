# Radiation Medical Exam MCP Server

A Model Context Protocol (MCP) server designed to create a structured database system for Navy Ionizing Radiation Medical Examinations (NAVMED 6470/13) used to monitor radiation workers for signs and symptoms of cancer and to clear them for work around ionizing radiation.

**⚠️ IMPORTANT: This is a DEMO server and is NOT HIPAA compliant. DO NOT use this in actual medical practice or with real patient data.**

## 🔐 Security Features

### Database Encryption
- **SQLCipher Integration**: All medical data encrypted at rest using SQLCipher
- **Transparent Encryption**: Database operations work seamlessly with encrypted data
- **Passphrase Protection**: Database requires passphrase for access
- **DoD-Grade Security**: Medical-grade protection for classified patient information

## Purpose

This MCP server provides a complete database system for managing NAVMED 6470/13 radiation medical examination data, including:
- **Encrypted SQLite Database**: All patient data protected with SQLCipher
- **Complete NAVMED Schema**: Full implementation of 6470/13 form structure
- **Structured Data Entry**: 10 related tables for comprehensive exam tracking
- **PDF Documentation Processing**: Official Navy radiation health documentation
- **Medical Examination Workflow**: From initial exam to final certification

## Features

### 🗄️ Encrypted Database System
- **SQLCipher Protection**: All medical data encrypted with passphrase
- **NAVMED 6470/13 Schema**: Complete database schema matching official form
- **Relational Structure**: 10 interconnected tables for comprehensive data management
- **Sample Data**: Test data for development and demonstration

### 📊 Database Tables
1. **examinations**: Main examination records (PE, RE, SE, TE types)
2. **examining_facilities**: Medical facility information
3. **medical_history**: Patient medical history (blocks 3-10)
4. **laboratory_findings**: Lab results (HCT, WBC, differential)
5. **urine_tests**: Urine testing results (blocks 12a, 12b)
6. **additional_studies**: Additional medical studies (block 13)
7. **physical_examination**: Physical exam findings (blocks 15-19)
8. **abnormal_findings**: Summary of abnormal findings (block 14)
9. **assessments**: Medical assessments and qualifications (blocks 20a, 20b)
10. **certifications**: Signatures and certifications (blocks 21-23)

### 📝 Database Operations
- **Complete CRUD**: Create, read, update, delete examination records
- **Complex Queries**: Retrieve complete examination data across all tables
- **Summary Reports**: Generate examination summaries for reporting
- **Schema Validation**: Ensure data integrity with proper relationships

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
- **Database Records**: Access to examination records via database queries
- **PDF Documents**: Full document access via `pdf://document/{filename}` URIs
- **Chapter Access**: Specific chapter content via `pdf://chapter/{filename}/{chapter_number}` URIs
- **Table Schemas**: Database schema information for all NAVMED tables

### Prompts
- **summarize-notes**: Creates summaries of all stored exam notes
- **explain-procedure**: Explains radiation medical exam procedures from official documentation

### Tools

#### Database Management
- **initialize-database**: Create and initialize the NAVMED database with encryption
  - Optional `include_sample_data` (boolean) - Include test examination data
  - Optional `force` (boolean) - Overwrite existing database
- **get-table-schema**: Get schema information for specific NAVMED tables
  - Required `table_name` - Name of the table to examine
- **add-exam-data**: Add data to any NAVMED examination table
  - Required `table_name` - Target table name
  - Required `data` - Dictionary of column values to insert
- **get-exam-data**: Retrieve data from NAVMED tables with filtering
  - Required `table_name` - Table to query
  - Optional `filters` - Dictionary of filter criteria
  - Optional `limit` - Maximum number of records to return
- **get-complete-exam**: Get complete examination with all related records
  - Required `exam_id` - Examination ID to retrieve
- **create-complete-exam**: Create complete examination with all sections
  - Required `examination_data` - Complete exam data structure
- **get-exam-summary**: Get examination summary for reporting
  - Optional `exam_id` - Specific examination ID
  - Optional `patient_ssn` - Patient SSN for all examinations

#### Documentation & Notes
- **add-note**: Add examination notes to the server
- **search-documentation**: Search through PDF documentation for specific terms

## Database Schema

### Core Examination Structure (NAVMED 6470/13)

```sql
-- Main examination record
examinations (
    exam_id, exam_type, exam_date, patient_last_name, patient_first_name,
    patient_middle_initial, patient_ssn, patient_dob, command_unit,
    rank_grade, department_service, facility_id
)

-- Medical history (blocks 3-10)
medical_history (
    history_id, exam_id, personal_history_cancer, history_radiation_exposure,
    history_anemia_hematuria, history_cancer_therapy, history_radiation_therapy,
    history_unsealed_sources, history_radiopharmaceutical_therapy,
    significant_illness_changes, significant_illness_details
)

-- Laboratory findings (block 11)
laboratory_findings (
    lab_id, exam_id, evaluation_date, hct_result, hct_lab_range,
    wbc_result, wbc_lab_range, wbc_facility, differential_required,
    differential_neutrophils, differential_lymphocytes, differential_monocytes,
    differential_eosinophils, differential_basophils
)

-- Additional tables: urine_tests, physical_examination, assessments, etc.
```

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

3. **Initialize encrypted database**:
   ```bash
   # The database will be created when first accessed via MCP tools
   # You'll be prompted for an encryption passphrase
   ```

4. **Add PDF documentation** (optional):
   - Place PDF files in `src/radiation_medical_exam/utils/instructions/`
   - Supported formats: PDF files with text content
   - Server will automatically detect and process new PDFs

5. **Configure Claude Desktop** using the configuration above

6. **Restart Claude Desktop** to load the server

## Dependencies

- **Python 3.12+**
- **mcp>=1.9.3**: Model Context Protocol SDK
- **pypdf>=4.0.0**: PDF processing and text extraction
- **aiofiles>=23.0.0**: Asynchronous file operations
- **cryptography>=41.0.0**: Encryption utilities
- **sqlcipher3-wheels>=0.5.4**: SQLCipher for database encryption

## Usage Examples

### Database Operations
```
"Initialize the NAVMED database with sample data"
"Show me the schema for the examinations table"
"Get all examination records"
"Add a new examination record for John Smith"
"Get complete examination data for exam ID 1"
"Generate an examination summary"
```

### Security Operations
```
"Create an encrypted database"
"Unlock the medical database"
"Check database encryption status"
```

### Documentation Search
```
"Search the documentation for 'dose limits'"
"What does Chapter 2 say about medical examinations?"
"Find information about radiation safety protocols"
```

## File Structure

```
radiation-medical-exam/
├── src/
│   └── radiation_medical_exam/
│       ├── server.py                 # Main MCP server implementation
│       ├── database/
│       │   ├── __init__.py
│       │   └── encrypted_db_manager.py # SQLCipher database management
│       ├── services/
│       │   ├── __init__.py
│       │   └── security_service.py   # Encryption key management
│       ├── utils/
│       │   ├── pdf_processor.py      # PDF processing utilities
│       │   ├── init_navmed_database.py # Database initialization
│       │   ├── navmed_database.py    # Database operations
│       │   └── instructions/         # PDF documentation storage
│       │       └── *.pdf            # Radiation health documentation
│       └── __init__.py
├── pyproject.toml                    # Project configuration
├── README.md                         # This file
└── test_*.py                         # Test scripts for encryption verification
```

## Security Architecture

### Database Encryption
- **SQLCipher**: Industry-standard database encryption
- **AES-256**: Strong encryption for medical data
- **HMAC Authentication**: Prevents unauthorized database modifications
- **Passphrase-Based**: User-controlled access to encrypted data

### Key Management
- **SecurityService**: Manages encryption keys and authentication
- **Cached Keys**: Secure in-memory key storage during operation
- **GUI Passphrase Entry**: Secure passphrase collection (when available)
- **Token Support**: Placeholder for future hardware token integration

### Data Protection
- **Transparent Encryption**: All database operations automatically encrypted
- **Always Encrypted**: Data never exists unencrypted on disk
- **Medical-Grade Security**: Suitable for classified patient information
- **DoD Standards**: Meets military medical data protection requirements

## Testing

The repository includes comprehensive test scripts:

- `test_sqlcipher.py`: Basic SQLCipher functionality testing
- `test_mcp_demo.py`: Complete MCP server workflow demonstration
- `test_minimal_encryption.py`: Minimal encryption verification
- `test_simple_debug.py`: Step-by-step SQLCipher testing

Run tests to verify installation:
```bash
python test_sqlcipher.py --all
python test_mcp_demo.py
```

## Migration Notes

This system has been upgraded from file-level encryption to transparent database encryption:

- **Previous**: Manual encryption/decryption of database files
- **Current**: SQLCipher transparent encryption with PRAGMA key commands
- **Benefits**: Better performance, always-encrypted data, transparent operations

## Disclaimer

This software is provided for demonstration and educational purposes only. It is not intended for use in actual medical practice and does not comply with HIPAA or other medical data protection regulations. Always consult with qualified medical professionals and use certified, compliant systems for actual radiation medical examinations.

## Contributing

This is a demonstration project. For production medical applications, ensure compliance with:
- HIPAA regulations
- Medical device software standards
- Institutional review board requirements
- Navy medical documentation standards
- Database encryption and security standards

## License

See LICENSE file for details.
