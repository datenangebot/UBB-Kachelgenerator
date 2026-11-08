# UBB Kachelgenerator

Interne PHP-Anwendung für quadratische Werbekacheln. Generator, Template-Editor und Exportarchiv laufen mit PHP 8.2+, Apache, HTML, CSS und Vanilla JavaScript. Keine Datenbank und kein Build-Schritt.

## Lokal starten

Docker Desktop starten, dann im Projektordner `docker compose up -d` ausführen und `http://localhost:8080` öffnen. Der Projektordner ist als Bind-Mount eingebunden; Codeänderungen sind ohne Image-Rebuild sichtbar. `docker compose logs web` zeigt das Anwendungslog.

## Plesk/Apache

Alle Projektdateien in ein durch HTTP Basic Auth geschütztes Verzeichnis kopieren und PHP 8.2 oder neuer einstellen. PHP-Erweiterungen `fileinfo` und `session` müssen aktiv sein. Der Webserver-Benutzer braucht Schreibrechte für `storage/backgrounds`, `storage/templates`, `storage/exports` und `assets/template-assets` sowie deren Unterordner. Eigentümer/Gruppe passend zum Plesk-PHP-Prozess setzen und etwa Verzeichnisse mit `775`, Dateien mit `664` betreiben. Keine pauschalen `777`-Rechte. Die `.htaccess`-Regeln schützen JSON und Projektdokumente bei Apache; auf anderen Webservern gleichwertige Regeln setzen. Für Exporte bis 80 MB pro Datei PHP-Limits `upload_max_filesize=80M` und `post_max_size=170M` setzen (PDF plus PNG-Vorschau im selben Request). Bild-Uploads bleiben in der Anwendung auf 20 MB begrenzt.

Ein vollständiges Backup umfasst `storage/backgrounds`, `storage/templates`, `storage/exports`, `assets/fonts` und `assets/template-assets`.

**Update einer bestehenden Installation:** Diese Verzeichnisse vor dem Update sichern. Bestehende Laufzeitdaten und eigene Schriften/Assets beim Kopieren erhalten; insbesondere `storage/templates/standard-magenta.json` nicht mit der ausgelieferten Beispieldatei überschreiben. Neue JS-Bibliotheken und den Schriftkatalog samt Schriftdateien ergänzen. Es gibt keine Migration und keine automatische Änderung vorhandener Exporte. Neue Metadaten werden ausschließlich bei neuen Exporten geschrieben. Ein Deployment darf keine Spiegelung mit Löschen unbekannter Dateien verwenden.

## Bedienung

Generator: Template wählen, dynamische Felder ausfüllen, Hintergrund wählen oder hochladen, Bildausschnitt einstellen, Texte bei Bedarf über ⚙ feinjustieren und als PNG, JPG oder PDF exportieren. Ein Standardfoto des Templates erscheint sofort und lässt sich im Generator ersetzen. „Template-Hintergrund verwenden“ stellt das Standardfoto samt Bildausschnitt wieder her. Der Export wird zuerst serverseitig gespeichert und danach heruntergeladen. Das Archiv zeigt alle Exporte, ohne Löschfunktion.

Templates: Neues Template anlegen oder vorhandenes bearbeiten. Elemente können auf dem Canvas gezogen und am Griff skaliert werden. Die rechte Spalte erlaubt präzise Werte. Bei Bild- und Foto-Elementen lassen sich JPG/PNG/WebP direkt hochladen. Bilder sind feste Template-Bestandteile; Fotos sind im Generator ersetzbare Standard-Hintergründe. Nach dem Upload das Template speichern. Jeder Upload erhält einen neuen Dateinamen, vorhandene Assets bleiben erhalten. Alternativ kann weiterhin ein vorhandener Pfad unter `assets/template-assets/` eingetragen werden. UTF-8-Dateinamen wie `assets/template-assets/2026_UBB-KiWo-Fördebühne.png` sind erlaubt.

Archiv: Neue Exporte enthalten den vollständigen Generatorzustand und eine Kopie des Templates. „Im Generator laden“ stellt Feldwerte, Bildwahl, Ausschnitt und Textanpassungen wieder her, auch wenn das ursprüngliche Template inzwischen geändert oder gelöscht wurde. Die Auswahl zeigt dann „Archivstand“. Ein weiterer Export erzeugt eine neue Datei; der ursprüngliche Export bleibt erhalten. Alte Exporte ohne vollständigen Zustand bleiben sichtbar und herunterladbar, erhalten aber keinen Ladebutton. Bilder werden über ihre dauerhaft gespeicherten Dateien referenziert; diese Dateien müssen bei Updates und Backups erhalten bleiben.

PDF: Das Seitenformat entspricht der Kachel (96 CSS-Pixel pro Zoll), 2× verdoppelt die Seitengröße und Bildauflösung. Text bleibt echter, auswählbarer PDF-Text; verwendete lokale Schriften werden als Teilmenge eingebettet. Zeilenumbrüche, automatische Schriftgröße, Drehung, Zeichenabstand, Ebenen und Bildausschnitt werden aus derselben Vorschau übernommen. Bild- und Flächenebenen werden gerastert. Durch unterschiedliche Kantenglättung sind PNG und gerendertes PDF nicht pixelidentisch.

Schriften: Liberation Sans, Serif und Mono (Regular/Bold) werden lokal mitgeliefert und in allen Exportformaten verwendet. Bestehende Angaben Arial/Helvetica, Times New Roman und Courier New werden ihren metrisch kompatiblen Liberation-Familien zugeordnet. Unbekannte Schriftangaben fallen wie in der Vorschau auf Liberation Sans zurück; der Editor zeigt die verwendete Familie. Weitere statische TTF/OTF-Dateien unter `assets/fonts/` ablegen und in `assets/fonts/fonts.json` mit Familie, optionalen Aliasnamen und Schnitten (`file`, `weight`) registrieren. Nur Schriften mit erlaubter Einbettung verwenden. Vorhandene Schriftdateien nicht ersetzen, damit archivierte Varianten reproduzierbar bleiben. Fehlende Zeichen verhindern den PDF-Export mit einer verständlichen Meldung, statt unbemerkt eine andere Schrift zu verwenden.

## Dateien und Entscheidungen

- `storage/templates/*.json`: Template-Modell Version 1. `standard-magenta` orientiert sich in Farbe, Textstruktur und Fotobereich an der Referenz.
- `storage/backgrounds/`: hochgeladene JPG/PNG/WebP-Bilder; Standardlimit 20 MB in `lib/config.php`.
- `storage/exports/YYYY/MM/`: Exportdateien mit JSON-Sidecar. PNG/JPG werden aus dem gleichen DOM wie die Vorschau gerendert. PDF erhält zusätzlich eine PNG-Vorschau (`.pdf.preview.png`).
- `assets/vendor/`: lokale Bootstrap- und html-to-image-Dateien. Quellen und Lizenzen stehen in `THIRD_PARTY.md`.

Das separate Original-UBB-Logo und die Hausschrift fehlen. Daher enthält das Starttemplate einen klaren `UBB`-Textplatzhalter in der Arial-kompatiblen Liberation Sans. Diesen später im Template-Editor durch ein `image`-Element mit freigegebenem lokalen Original-Asset ersetzen. Die Referenzgrafik wird nicht als fertiger Kachelhintergrund verwendet.

Leeres neues Template verwendet 1138 × 1138 px als Vorschlag. Freie Template-IDs werden aus Namen abgeleitet; bei gleicher ID meldet der Server einen Konflikt. Das Editor-Preview zeigt für ein `photo`-Element eine neutrale Fläche, bis im Generator ein Foto gewählt wird. Frontend-Entwürfe sind flüchtig; erst Template-Speichern oder Export archiviert Daten.

## Tests

`python3 tests/smoke.py` prüft die API im laufenden Docker-System. `tests/browser.py`, `tests/editor.py`, `tests/editor_drag.py`, `tests/uploads.py` und `tests/final_export.py` sind optionale Browser-Abnahmeskripte mit Playwright für Python und Chromium als externem Testwerkzeug. Playwright gehört nicht zur Anwendung und wird für Entwicklung oder Betrieb nicht benötigt. Der Browser-Testexport `UBB-Testexport.png` samt Sidecar bleibt als geprüftes Archivbeispiel erhalten.

`tests/export_roundtrip.py` prüft zusätzlich Editor-Uploads, Standardfotos, PNG/PDF-Vergleich, echte eingebettete PDF-Schriften, Wiederherstellung nach Template-Löschung, erneuten Export und Altbestände ohne Ladebutton. Benötigt Playwright, Pillow und PyMuPDF. Optional `BROWSER_EXECUTABLE` für einen installierten Chromium-Browser setzen. Der Test löscht nur seine eindeutig benannten Testdaten und überprüft bestehende Archivdateien per SHA-256.
