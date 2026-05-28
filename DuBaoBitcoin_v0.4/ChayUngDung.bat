@echo off
chcp 65001 >nul
title Dự Báo Giá Bitcoin

echo ========================================== HỆ THỐNG ĐANG KHỞI CHẠY TỰ ĐỘNG ==========================================
echo.

:: Chỉ định đường dẫn lõi Conda nằm ngay cùng cấp vách với file .bat này
set "EMBEDDED_CONDA=%~dp0..\miniconda_core"

:: 1. Kiểm tra xem folder lõi miniconda_core đã có ở đây chưa
if not exist "%EMBEDDED_CONDA%\Scripts\conda.exe" (
    echo [LỖI] Không tìm thấy thư mục lõi '%EMBEDDED_CONDA%'.
    echo Hãy đảm bảo bạn đã copy thư mục Miniconda 3 vào đây và đổi tên thành 'miniconda_core'.
    echo.
    pause
    exit /b
)

echo [OK] Đã phát hiện lõi Conda độc lập cùng cấp dự án.
echo [INFO] Đang nạp cấu hình hệ thống...
echo.
echo ---------------------------------------------------------------------------------------------------------------------
echo.

:: Khởi chạy cấu hình conda trực tiếp từ folder con này
call "%EMBEDDED_CONDA%\Scripts\activate.bat" "%EMBEDDED_CONDA%"

:: Kích hoạt môi trường DeepLearning có sẵn trong lõi
call conda activate DeepLearning

:: Tự động kiểm tra và đồng bộ thư viện từ ThuVien.txt nếu có thay đổi
if exist ThuVien.txt (
    echo [INFO] Đang quét và kiểm tra đầy đủ các thư viện cần thiết...
    echo.
    echo ---------------------------------------------------------------------------------------------------------------------
    echo.
    call pip install -r ThuVien.txt
    echo.
    echo ---------------------------------------------------------------------------------------------------------------------
    echo.
    echo [OK] Quá trình đồng bộ thư viện hoàn tất.
)
echo.

:: Khởi chạy giao diện ứng dụng Streamlit
echo [INFO] Đang khởi động giao diện đồ án trên trình duyệt...
echo.
echo ---------------------------------------------------------------------------------------------------------------------
echo.
call streamlit run UngDung.py

echo.
echo [INFO] Ứng dụng đã đóng.
pause
