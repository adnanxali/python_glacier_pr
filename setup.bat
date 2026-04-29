@echo off
echo ==========================================
echo  Glacier Detection Flask Setup
echo ==========================================
echo.

echo Creating project structure...
echo.

REM Create main directories
mkdir models 2>nul
mkdir database 2>nul
mkdir static 2>nul
mkdir static\uploads 2>nul
mkdir templates 2>nul
mkdir utils 2>nul

echo [✓] Folders created successfully
echo.

REM Create empty Python files
type nul > app.py
type nul > config.py
type nul > utils\__init__.py
type nul > utils\database.py
type nul > utils\glacier_analysis.py
type nul > utils\gemini_integration.py

echo [✓] Python files created
echo.

REM Create empty HTML template files
type nul > templates\index.html
type nul > templates\login.html
type nul > templates\signup.html
type nul > templates\dashboard.html
type nul > templates\admin_login.html
type nul > templates\admin_dashboard.html

echo [✓] Template files created
echo.

REM Create requirements.txt
(
echo flask==3.0.0
echo ultralytics==8.1.0
echo opencv-python==4.8.1.78
echo numpy==1.24.3
echo joblib==1.3.2
echo google-generativeai==0.3.1
echo Pillow==10.1.0
echo werkzeug==3.0.1
) > requirements.txt

echo [✓] requirements.txt created
echo.

echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo Project structure created successfully!
echo.
echo Next steps:
echo 1. Copy your bestglacier.pt to models/ folder
echo 2. Copy your hybrid_risk_model.pkl to models/ folder
echo 3. Fill in the code for each file
echo 4. Run: pip install -r requirements.txt
echo 5. Run: python app.py
echo.
pause