# Practice 05 Constitution

## Core Principles

### I. Stack: Python 3 stdlib only
- The MCP Sudoku server is at mcp/sudoku/index.py and must use only the Python 3 standard library (no third-party dependencies).

### II. Visualization: Static HTML+CSS
- UI is static HTML with inline CSS. Do not add external JS/CSS libraries or frameworks.

### III. Backward compatibility: stable MCP contracts
- Existing call contracts for sudoku.hint and sudoku.patterns must not break. Do not introduce new required flags; defaults must preserve current behavior.

### IV. Testing: mandatory verification
- Every change must pass: python3 scripts/verify.py. The same verification runs via the auto-verify.js hook; changes failing verification must be fixed before merge.

## Governance
- This constitution is authoritative for practice_05. Changes to these principles must be documented and reviewed.

Version: 1.0.0 | Ratified: 2026-11-02 | Last Amended: 2026-11-02
