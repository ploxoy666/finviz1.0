Set oWS = WScript.CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")

' Получаем путь к текущей директории скрипта
sScriptPath = oFSO.GetParentFolderName(WScript.ScriptFullName)

' Создаем ярлык на рабочем столе
sLinkFile = oWS.SpecialFolders("Desktop") & "\FinvizPro.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = sScriptPath & "\start_finvizpro.bat"
    oLink.WorkingDirectory = sScriptPath
    oLink.Description = "Запуск FinvizPro локально"
    oLink.IconLocation = "C:\Windows\System32\imageres.dll,1"
oLink.Save

WScript.Echo "Ярлык FinvizPro создан на рабочем столе!"
