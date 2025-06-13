@echo off
echo 🚀 Uploading ATLAS to GitHub...

REM Initialize git repository
git init

REM Add all files (except those in .gitignore)
git add .

REM Commit the initial version
git commit -m "🤖 Initial ATLAS Trading Assistant commit

Features:
- ✅ Autonomous AI trading bot
- ✅ FastAPI proxy for secure API calls  
- ✅ Streamlit desktop interface
- ✅ Alpaca Markets integration
- ✅ Financial Modeling Prep data
- ✅ OpenAI-powered trading decisions
- ✅ 24/7 crypto trading support"

echo.
echo ✅ Repository initialized and committed!
echo.
echo 📋 NEXT STEPS:
echo 1. Go to https://github.com/new
echo 2. Create a new repository called "ATLAS"
echo 3. Copy the commands GitHub gives you, OR run:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/ATLAS.git
echo    git branch -M main  
echo    git push -u origin main
echo.
echo 🎉 Your ATLAS trading bot will be live on GitHub!

pause 