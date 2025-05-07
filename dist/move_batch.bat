@echo off
REM 將 FAQ Guide/_internal/config 資料夾搬到 FAQ Guide 資料夾內
move "FAQ Guide\_internal\config" "FAQ Guide\"

REM 將 FAQ Guide/_internal/images 資料夾搬到 FAQ Guide 資料夾內
move "FAQ Guide\_internal\images" "FAQ Guide\"

REM 將 FAQ Guide/_internal/filter.xml 檔案搬到 FAQ Guide 資料夾內
move "FAQ Guide\_internal\filter.xml" "FAQ Guide\"
