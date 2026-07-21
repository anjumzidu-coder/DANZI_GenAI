# S&S AI Tool (Web Console)

A modern Streamlit app to replicate and upgrade your S&S analysis workflow.

## What it does
- Upload Excel (`.xlsx`), CSV, PDF, and PowerPoint (`.pptx`, `.ppt`) files
- Read all sheets and preview data
- Auto-generate profile stats and quality checks
- Ask AI questions about your document/data
- Produce executive summary + action items
- Detects S&S tracker profile (`Summary`, `Lists`, `Product 1`) and highlights missing sheets
- Includes quick analysis buttons for requirement gaps and executive summary

## Quick start
1. Create a virtual environment and activate it.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set your AI credentials.
4. Run app:
   - `streamlit run app.py`

## Team access on corporate network
1. Keep this app running on a machine reachable by your teammates.
2. Start with PowerShell:
   - `./start_team_access.ps1`
3. Share the printed Team URL (example: `http://10.x.x.x:8501`).
4. Ensure Windows Firewall allows inbound traffic on port `8501`.

Note: For permanent shared usage, deploy to an internal VM or container platform.

## Migration path from your existing Excel tool
1. Upload the same workbook in this app.
2. Compare outputs between Excel and app results.
3. Fine-tune prompts/rules in `src/analyzer.py`.
4. Add any fixed business formulas in `src/rules.py`.

## Recommended first test
1. Open the app.
2. Upload `UAT_MAT_v1.3.3_05-26-2026.xlsm`.
3. Select `Product 1` sheet.
4. Click `Quick Analysis: Requirement Gaps`.

## PowerPoint note
- `.pptx` is parsed directly.
- `.ppt` is auto-converted to `.pptx` on Windows when PowerPoint is installed.

## Next upgrades
- Add user login and saved runs
- Export reports to PDF/Email/WhatsApp
- Background scheduling with task runner
