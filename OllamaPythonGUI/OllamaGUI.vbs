Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the current directory
strCurrentDirectory = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Path to the batch file
strBatchFile = strCurrentDirectory & "\OllamaGUI.bat"

' Path to the Ollama serve command
strOllamaServe = "cmd /c ollama serve"

' Run the batch file in the background
objShell.Run Chr(34) & strBatchFile & Chr(34), 0, False

' Run the Ollama serve command in the background
objShell.Run strOllamaServe, 0, False
