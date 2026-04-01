@echo off
echo Starting MongoDB...
echo.
echo Make sure MongoDB is installed. If not, download from:
echo https://www.mongodb.com/try/download/community
echo.

REM Try to start MongoDB service
net start MongoDB

if %errorlevel% neq 0 (
    echo.
    echo MongoDB service not found or failed to start.
    echo.
    echo Trying to start mongod directly...
    start "MongoDB" mongod --dbpath=C:\data\db
    
    if %errorlevel% neq 0 (
        echo.
        echo Failed to start MongoDB.
        echo Please ensure MongoDB is installed and the data directory exists.
        echo Default data directory: C:\data\db
        echo.
        echo Create it with: mkdir C:\data\db
        pause
        exit /b 1
    )
)

echo.
echo MongoDB started successfully!
echo.
pause
