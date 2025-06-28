# Project Rules and Conventions

## Core Principles

### 1. Documentation First
- **All changes must be documented**: When creating new files, directories, or major functionality, update README.md immediately
- **Rules file maintenance**: This rules.md file must be updated when new conventions are established
- **Code comments**: All complex logic must include clear comments explaining purpose and approach
- **Commit messages**: Use conventional commit format with Memex attribution

### 2. Modular Architecture
- **Separation of concerns**: Each module has a single, well-defined responsibility
- **Interface consistency**: All extractors implement the same interface pattern
- **Service-ready design**: Code must be designed for eventual service deployment
- **Error isolation**: Failures in one component should not cascade to others

### 3. Development Standards

#### File Structure
- **Source code**: All implementation code goes in `src/` directory
- **Tests**: All test files go in `tests/` directory with matching structure
- **Output**: Generated files go in `output/` directory (gitignored)
- **Logs**: Application logs go in `logs/` directory (gitignored)

#### Naming Conventions
- **Files**: snake_case for all Python files
- **Classes**: PascalCase for class names
- **Functions**: snake_case for function names
- **Constants**: UPPER_CASE for constants
- **Directories**: lowercase with underscores

#### Python Standards
- **Virtual environment**: Always use `.venv` in project root
- **Dependencies**: Use `uv` for package management
- **Type hints**: All public functions must include type hints
- **Docstrings**: All public functions must include docstrings
- **Error handling**: Use explicit exception handling, no bare except blocks

### 4. Git Standards
- **Branch naming**: `feature/description`, `bugfix/description`, `docs/description`
- **Commit format**: `type(scope): description\n\n🤖 Generated with [Memex](https://memex.tech)\nCo-Authored-By: Memex <noreply@memex.tech>`
- **Commit frequency**: Commit early and often
- **No secrets**: Never commit API keys, passwords, or sensitive data

### 5. Legal and Ethical Guidelines
- **Terms of service**: Respect all website terms of service
- **Rate limiting**: Implement appropriate delays between requests
- **User agent**: Always identify as automated tool with contact information
- **Data handling**: Only extract publicly available content
- **Attribution**: Maintain proper attribution for source materials

### 6. Quality Assurance
- **Testing**: All extractors must have corresponding tests
- **Validation**: Verify extracted audio quality before saving
- **Error logging**: Log all errors with sufficient context for debugging
- **Resource cleanup**: Always clean up temporary files and browser sessions

### 7. Configuration Management
- **Environment variables**: Use environment variables for configuration
- **Default values**: Provide sensible defaults for all configuration options
- **Validation**: Validate all configuration at startup
- **Documentation**: Document all configuration options in README

### 8. Service Deployment Readiness
- **Containerization**: Code must be containerizable
- **Health checks**: Implement health check endpoints
- **Metrics**: Include basic metrics collection
- **Graceful shutdown**: Handle shutdown signals properly

## File Creation Rules

### When creating new files:
1. **Update README.md** with new file in project structure
2. **Add to .gitignore** if file should not be tracked
3. **Create corresponding test file** if implementing new functionality
4. **Update requirements.txt** if adding new dependencies

### When creating new directories:
1. **Update README.md** project structure section
2. **Add __init__.py** for Python packages
3. **Document purpose** in this rules file if establishing new convention

## Change Log
- **2025-06-27**: Initial rules file created
- **2025-06-27**: Established project structure and naming conventions
- **2025-06-27**: Phase 3 - Added congressional metadata system (data/, models/, enrichment/)
- **2025-06-27**: Phase 4 - Congress.gov API integration with priority committee expansion
- **2025-06-27**: Phase 5 - Whisper integration and complete transcription pipeline (transcription/)
- **2025-06-27**: Phase 6A - Human review system with React frontend and FastAPI backend (review/)
- **2025-06-28**: Phase 6B - Voice recognition enhancement with automated sample collection and speaker modeling (voice/)
- **2025-06-28**: Phase 6C - Advanced learning & feedback integration with pattern analysis, threshold optimization, and predictive identification (learning/)
- **2025-06-28**: Phase 6C Improvements - Enhanced error handling, performance optimization, SQLite fixes, and production readiness (error_handler.py, performance_optimizer.py)
- **2025-06-28**: Phase 7 Planning - Automated data synchronization and enhanced UI workflow research and implementation planning (AUTOMATED_SYNC_AND_UI_PLAN.md, PHASE_7_IMPLEMENTATION_PLAN.md)

---

## Quick Reference

### Adding a new extractor:
1. Create `src/extractors/new_extractor.py`
2. Implement `BaseExtractor` interface
3. Add tests in `tests/extractors/test_new_extractor.py`  
4. Update README.md project structure
5. Document in extractor registry

### Adding a new dependency:
1. Install with `uv pip install package_name`
2. Update requirements.txt with `uv pip freeze > requirements.txt`
3. Document usage in README.md if user-facing

### Making configuration changes:
1. Update `src/utils/config.py`
2. Document in README.md usage section
3. Add validation in config loader
4. Update environment variable documentation

---
*Last updated: 2025-06-27*
*Must be updated when establishing new conventions*