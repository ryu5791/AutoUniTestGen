@echo off
REM AutoUniTestGen実行用バッチファイル（Windows用）

setlocal

REM Pythonのパスを設定（必要に応じて変更してください）
set PYTHON_EXE=python

REM スクリプトのディレクトリに移動
cd /d %~dp0

REM PYTHONPATHを設定
set PYTHONPATH=%cd%;%cd%\src;%PYTHONPATH%

REM main.pyを実行
%PYTHON_EXE% main.py %*

endlocal
