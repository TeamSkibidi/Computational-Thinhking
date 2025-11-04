@echo off
echo ========================================
echo MySQL Password Reset Script
echo ========================================
echo.
echo Step 1: Stopping MySQL service...
net stop MySQL80
echo.
echo Step 2: Starting MySQL with skip-grant-tables...
start "" "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --skip-grant-tables --shared-memory
timeout /t 5
echo.
echo Step 3: Connecting to MySQL and resetting password...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root --skip-password -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'Root@123456'; FLUSH PRIVILEGES;"
echo.
echo Step 4: Stopping MySQL process...
taskkill /F /IM mysqld.exe
timeout /t 2
echo.
echo Step 5: Starting MySQL service normally...
net start MySQL80
echo.
echo ========================================
echo Done! Password is now: Root@123456
echo ========================================
pause
