@echo off
chcp 65001 >nul
echo ========================================
echo 🗑️  RESET DATABASE - XÓA TẤT CẢ DỮ LIỆU
echo ========================================
echo.
echo Đang xóa tất cả dữ liệu trong database 'travel'...
echo.

"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p620121 -e "USE travel; SET FOREIGN_KEY_CHECKS = 0; TRUNCATE TABLE places; TRUNCATE TABLE addresses; SET FOREIGN_KEY_CHECKS = 1;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Đã xóa hết dữ liệu thành công!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ Lỗi khi xóa dữ liệu!
    echo ========================================
)

echo.
pause
