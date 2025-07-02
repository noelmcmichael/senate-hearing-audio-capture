# Phase 7C Issues Investigation

## Issues Identified:

1. **Limited Hearings per Committee**: Only 2 hearings per committee (should be more from 2025 Congress)
2. **View Details Button Not Working**: No response when clicked
3. **Capture Button Error**: 422 Unprocessable Entity error
4. **Poor Error Handling**: "[object Object]" instead of readable error messages

## Investigation Plan:

1. Check database contents for hearing count
2. Investigate 422 error from capture API
3. Fix error handling in frontend
4. Check view details functionality
5. Add more demo hearings if needed