@echo off
chcp 65001 >nul
echo ========================================
echo 🔄 RESET DATABASE - TẠO LẠI HOÀN TOÀN
echo ========================================
echo.
echo Đang drop và tạo lại database 'travel'...
echo.

"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pRoot@123456 -e "DROP DATABASE IF EXISTS travel; CREATE DATABASE travel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Đã tạo lại database 'travel'
    echo.
    echo Đang tạo bảng addresses...
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pRoot@123456 travel < "../DB/1_addresses.sql"
    
    echo Đang tạo bảng places...
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -pRoot@123456 travel < "../DB/2_places.sql"
    
    echo.
    echo ========================================
    echo ✅ Đã reset database thành công!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ Lỗi khi tạo lại database!
    echo ========================================
)

echo.
pause
