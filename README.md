Skripte zur Interaktion mit der SRW-Implementierung von fiverx.link.

Die Skripte dienen dazu, eingereichte Rezeptdaten vom fiverx.link-Server
abzurufen bzw. Rezeptdaten dorthin hochzuladen (letzteres ist nur zum
Testen gedacht).

Alle Skripte laufen mit Python >= 3.6.


## Installation

    pip install --extra-index-url=https://www.steinreichwald.net/srw.link/dependencies/  -e .


## fiverx-fetch-prescriptions

Benutzung:

    fiverx-fetch-prescriptions [--config=fiverx.ini] [--since SINCE] export_dir

Dieses Skript ruft die auf dem Server gespeicherten fiverx-Daten ab und
erstellt automatisch ein Unterverzeichnis des angebenen Export-Ordners.
Das Unterverzeichnis enthält das aktuelle Datum und die aktuelle Uhrzeit
(z.B. "2015-10-01T08_52_42+02_00").

Standardmäßig werden nur noch nicht abgerufene Rezepte abgeholt (Export-Datum
in der Datenbank nicht gesetzt, Status ist VOR_PRUEFUNG, HINWEIS oder
VERBESSERBAR).

Mit dem Parameter "--since" (z.B. "--since=2015-10-01") werden *zusätzlich*
auch bereits exportierte Rezepte exportiert, deren Exportdatum nach dem
angegebenen Datum (im obigen Beispiel der 1. Oktober 2015) liegt und deren
Status VOR_ABRECHNUNG ist.

Die Konfiguration (Zugangsdaten, URL des Webservices) wird aus der angegebenen
Konfigurationsdatei gelesen (siehe auch "fiverx.ini.sample"). Falls der
"--config"-Parameter beim Aufruf nicht angegeben wurde, verwendet das Programm
standardmäßig die Datei "fiverx.ini" aus dem aktuellen Verzeichnis.

