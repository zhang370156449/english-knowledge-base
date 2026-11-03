@echo off
chcp 65001 >nul
title LexiFragment - 自动扫描并同步本地知识库
echo ========================================================
echo   LexiFragment 知识库索引自动扫描与同步器
echo ========================================================
echo.
echo 正在扫描本地所有作者视频目录、articles 与 books 文件夹...
python "%~dp0sync_library.py"
echo.
echo 同步完成！刷新网页即可查看到最新添加的内容。
pause
