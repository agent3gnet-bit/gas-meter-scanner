; GasMeterReader Installer
!define APP_NAME "GasMeterReader"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Gas Service"
!define APP_EXE "GasMeterReader.exe"

Unicode true
Name "${APP_NAME}"
OutFile "GasMeterReader_Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    
    File "${APP_DIR}\${APP_EXE}"
    File "reference_db.xlsx"
    
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
    
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "UninstallString" "$INSTDIR\uninst.exe"
    
    WriteUninstaller "$INSTDIR\uninst.exe"
    
    SetDetailsPrint none
    MessageBox MB_ICONINFORMATION "${APP_NAME} successfully installed!"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\uninst.exe"
    Delete "$INSTDIR\reference_db.xlsx"
    Delete "$INSTDIR\history.xlsx"
    
    RMDir "$INSTDIR"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    
    MessageBox MB_ICONINFORMATION "${APP_NAME} successfully uninstalled"
SectionEnd
