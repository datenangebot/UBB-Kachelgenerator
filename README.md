# UBB Kachelgenerator

Interne PHP-Anwendung für quadratische Werbekacheln. Generator, Template-Editor und Exportarchiv laufen mit PHP 8.2+, Apache, HTML, CSS und Vanilla JavaScript. Keine Datenbank und kein Build-Schritt.

## Lokal starten

Docker Desktop starten, dann im Projektordner `docker compose up -d` ausführen und `http://localhost:8080` öffnen. Der Projektordner ist als Bind-Mount eingebunden; Codeänderungen sind ohne Image-Rebuild sichtbar. `docker compose logs web` zeigt das Anwendungslog.

## Plesk/Apache

Alle Projektdateien in ein durch HTTP Basic Auth geschütztes Verzeichnis kopieren und PHP 8.2 oder neuer einstellen. PHP-Erweiterungen `fileinfo` und `session` müssen aktiv sein. Der Webserver-Benutzer braucht Schreibrechte für `storage/backgrounds`, `storage/templates` und `storage/exports` sowie deren Unterordner. Eigentümer/Gruppe passend zum Plesk-PHP-Prozess setzen und etwa Verzeichnisse mit `775`, Dateien mit `664` betreiben. Keine pauschalen `777`-Rechte. Die `.htaccess`-Regeln schützen JSON und Projektdokumente bei Apache; auf anderen Webservern gleichwertige Regeln setzen. Für Exporte bis 80 MB PHP-Limits `upload_max_filesize=80M` und `post_max_size=90M` setzen. Hintergrund-Uploads bleiben in der Anwendung auf 20 MB begrenzt.

Ein vollständiges Backup umfasst `storage/backgrounds`, `storage/templates`, `storage/exports` sowie später ergänzte Dateien unter `assets/fonts` und `assets/template-assets`.

## Bedienung

Generator: Template wählen, dynamische Felder ausfüllen, Hintergrund wählen oder hochladen, Bildausschnitt einstellen, Texte bei Bedarf über ⚙ feinjustieren und exportieren. Der Export wird zuerst serverseitig gespeichert und danach heruntergeladen. Das Archiv zeigt alle Exporte, ohne Löschfunktion.

Templates: Neues Template anlegen oder vorhandenes bearbeiten. Elemente können auf dem Canvas gezogen und am Griff skaliert werden. Die rechte Spalte erlaubt präzise Werte. Für ein Bild-Element muss vorher eine lokale Datei unter `assets/template-assets/` liegen; der Pfad wird dort eingetragen. Nur vorhandene Dateien in diesem Verzeichnis werden akzeptiert.

## Dateien und Entscheidungen

- `storage/templates/*.json`: Template-Modell Version 1. `standard-magenta` orientiert sich in Farbe, Textstruktur und Fotobereich an der Referenz.
- `storage/backgrounds/`: hochgeladene JPG/PNG/WebP-Bilder; Standardlimit 20 MB in `lib/config.php`.
- `storage/exports/YYYY/MM/`: Exportdateien mit JSON-Sidecar. PNG/JPG werden aus dem gleichen DOM wie die Vorschau gerendert.
- `assets/vendor/`: lokale Bootstrap- und html-to-image-Dateien. Quellen und Lizenzen stehen in `THIRD_PARTY.md`.

Das separate Original-UBB-Logo und die Hausschrift fehlen. Daher enthält das Starttemplate einen klaren `UBB`-Textplatzhalter in Arial. Diesen später im Template-Editor durch ein `image`-Element mit freigegebenem lokalen Original-Asset ersetzen. Die Referenzgrafik wird nicht als fertiger Kachelhintergrund verwendet.

Leeres neues Template verwendet 1138 × 1138 px als Vorschlag. Freie Template-IDs werden aus Namen abgeleitet; bei gleicher ID meldet der Server einen Konflikt. Das Editor-Preview zeigt für ein `photo`-Element eine neutrale Fläche, bis im Generator ein Foto gewählt wird. Frontend-Entwürfe sind flüchtig; erst Template-Speichern oder Export archiviert Daten.

## Tests

`python3 tests/smoke.py` prüft die API im laufenden Docker-System. `tests/browser.py`, `tests/editor.py`, `tests/editor_drag.py`, `tests/uploads.py` und `tests/final_export.py` sind optionale Browser-Abnahmeskripte mit Playwright für Python und Chromium als externem Testwerkzeug. Playwright gehört nicht zur Anwendung und wird für Entwicklung oder Betrieb nicht benötigt. Der Browser-Testexport `UBB-Testexport.png` samt Sidecar bleibt als geprüftes Archivbeispiel erhalten.
