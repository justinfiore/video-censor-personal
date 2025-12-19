' Launch the Video Censor Personal desktop UI on Windows
' 
' This VBScript runs the batch launcher silently without showing a console window.
' Double-click this file in Windows Explorer to launch the UI.
'
' Requires: Python 3.13 or higher
'
' Usage: double-click launch-ui.vbs

Set objShell = CreateObject("WScript.Shell")
strScriptPath = objShell.CurrentDirectory

' Run the batch script silently (0 = hidden window)
' The batch script will perform version checking and show errors if needed
objShell.Run Chr(34) & strScriptPath & "\launch-ui.bat" & Chr(34), 0, False
