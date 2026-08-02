@echo off
:: Ouvre les ports Booktime pour accès depuis un autre PC (à lancer en admin)
netsh advfirewall firewall delete rule name="BOOKTIME Frontend 3000" >nul 2>&1
netsh advfirewall firewall delete rule name="BOOKTIME Backend 8001" >nul 2>&1
netsh advfirewall firewall add rule name="BOOKTIME Frontend 3000" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="BOOKTIME Backend 8001" dir=in action=allow protocol=TCP localport=8001
echo.
echo Ports 3000 et 8001 autorises.
echo Sur l'autre PC, ouvrir : http://192.168.1.167:3000
echo.
pause
