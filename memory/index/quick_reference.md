# NAVMED Quick Reference Guide

## 🚀 **Essential Info At-A-Glance**

### **Project Status**
- **Current Branch:** `dev-docker`
- **Last Major Update:** 2025-06-05 (Complete Refactoring)
- **Production Ready:** ✅ Yes
- **Docker Ready:** 🚧 In Development

### **Quick Start Commands**

```bash
# Initialize database
python -m mcp_radiation-medical-exam initialize-database

# View examination data
python -m mcp_radiation-medical-exam get-exam-data --table examinations

# Get complete exam
python -m mcp_radiation-medical-exam get-complete-exam --exam-id 1
```

### **Key File Locations**

```
src/radiation_medical_exam/
├── server.py               # Original server (858 lines)
├── server_refactored.py    # New clean server (300 lines)
├── handlers/               # Tool, resource, prompt handlers
├── services/               # Business logic and validation
├── database/               # Repository and schema management
└── utils/                  # PDF processing and utilities
```

### **Database Schema (10 Tables)**

| Table | Purpose | NAVMED Block |
|-------|---------|--------------|
| `examinations` | Main exam record | Header info |
| `examining_facilities` | Medical facilities | - |
| `medical_history` | Patient history | Blocks 3-10 |
| `laboratory_findings` | Lab results | Block 11 |
| `urine_tests` | Urine testing | Block 12 |
| `additional_studies` | Extra tests | Block 13 |
| `physical_examination` | Physical findings | Blocks 15-19 |
| `abnormal_findings` | Abnormalities | Block 14 |
| `assessments` | Medical assessment | Blocks 20a, 20b |
| `certifications` | Signatures | Blocks 21-23 |

### **MCP Tools Available**

| Tool | Purpose | Example |
|------|---------|---------|
| `initialize-database` | Setup database | `{"force": true}` |
| `get-table-schema` | View table structure | `{"table_name": "examinations"}` |
| `add-exam-data` | Add single record | `{"table_name": "examinations", "data": {...}}` |
| `get-exam-data` | Query records | `{"table_name": "examinations", "limit": 10}` |
| `create-complete-exam` | Add full exam | `{"examination_data": {...}}` |
| `get-complete-exam` | Get full exam | `{"exam_id": 1}` |
| `get-exam-summary` | Get summary | `{"patient_ssn": "123-45-6789"}` |
| `search-documentation` | Search PDFs | `{"search_term": "radiation"}` |
| `add-note` | Add notes | `{"name": "note1", "content": "..."}` |

### **Test Data Available**

| Patient | Exam Type | SSN | Status |
|---------|-----------|-----|--------|
| John Smith | PE (Physical) | 123-45-6789 | Complete |
| Maria Rodriguez | RE (Re-exam) | 234-56-7890 | Complete |
| David Johnson | SE (Special) | 345-67-8901 | Complete |
| Lisa Thompson | TE (Termination) | 456-78-9012 | Complete |
| Robert Williams | PE (Physical) | 567-89-0123 | Complete |

### **Validation Rules**

```python
# Exam Types
PE = "Physical Examination"
RE = "Re-examination" 
SE = "Special Examination"
TE = "Termination Examination"

# Status Values
NML = "Normal"
ABN = "Abnormal"
NE = "Not Examined"

# Assessment Values
PQ = "Physically Qualified"
NPQ = "Not Physically Qualified"

# SSN Format: XXX-XX-XXXX
# Date Format: YYYY-MM-DD
```

### **Common Workflows**

#### **Create New Examination**
1. Use `create-complete-exam` with full examination data
2. Validation automatically applied
3. Returns exam_id for future reference

#### **Review Examination**
1. Use `get-complete-exam` with exam_id
2. Use `get-exam-summary` for overview
3. Check all required fields completed

#### **Search Documentation**
1. Use `search-documentation` with medical terms
2. Search specific document or all PDFs
3. Returns contextual results

### **Architecture Patterns**

- **Repository Pattern** - Clean data access
- **Service Layer** - Business logic separation
- **Handler Pattern** - MCP tool organization
- **Validation Engine** - NAVMED compliance
- **Factory Pattern** - Database initialization

### **Environment Variables**

```bash
DB_PATH=src/radiation_medical_exam/data/navmed_radiation_exam.db
INSTRUCTIONS_PATH=src/radiation_medical_exam/utils/instructions
LOG_LEVEL=INFO
```

### **Known Issues & Solutions**

| Issue | Solution |
|-------|----------|
| Database locked | Use `force=true` in initialize-database |
| Validation errors | Check NAVMED format requirements |
| PDF not found | Verify instructions path exists |
| Import errors | Check Python path and module structure |

### **Next Development Priorities**

1. **Docker Containerization** (Current Focus)
2. **Unit Testing** - Service and handler tests
3. **Integration Testing** - End-to-end workflows
4. **Performance Optimization** - Query optimization
5. **Audit Logging** - Medical compliance tracking

---

**🚨 Remember:** Always check validation rules before adding data!  
**📖 For Details:** See `memory/architecture/system_overview.md`  
**🔧 For Setup:** See `memory/workflows/deployment_process.md` 