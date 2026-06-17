@echo off
chcp 65001 > nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Hệ thống Dinh dưỡng Graph-RAG (NGR-Engine)
cls
echo ==========================================================
echo   ĐANG KÍCH HOẠT HỆ THỐNG HYBRID GRAPH-RAG TỰ ĐỘNG...
echo ==========================================================
echo.

echo -^> Đang khởi động Backend FastAPI (Uvicorn)...
start "NGR - Backend Server" cmd /k "chcp 65001 > nul && set PYTHONUTF8=1&& set PYTHONIOENCODING=utf-8&& cd /d D:\KHOALUAN9\nutrition_graph_rag\backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --reload"

timeout /t 3 /nobreak > nul

echo -^> Đang khởi động Frontend Streamlit Interface...
start "NGR - Frontend Web" cmd /k "chcp 65001 > nul && set PYTHONUTF8=1&& set PYTHONIOENCODING=utf-8&& set NUTRITION_API_BASE=http://127.0.0.1:8000&& cd /d D:\KHOALUAN9\nutrition_graph_rag\frontend && ..\venv\Scripts\python.exe -m streamlit run app.py"

echo.
echo ==========================================================
echo   KÍCH HOẠT THÀNH CÔNG! VUI LÒNG KIỂM TRA CẢ 2 CỬA SỔ.
echo ==========================================================
timeout /t 5
