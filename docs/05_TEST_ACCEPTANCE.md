# 05 – Tests und Abnahmekriterien

## Lokaler Start

- `docker compose up -d` startet ohne zusätzliche manuelle Installationen.
- Anwendung unter `http://localhost:8080` erreichbar.
- Bind-Mount sorgt dafür, dass Quellcodeänderungen sofort sichtbar sind.

## PHP

- Alle `.php`-Dateien bestehen `php -l`.
- Kein unkontrollierter Warning/Notice-Spam im Log beim normalen Workflow.

## Generator

- Templatewechsel aktualisiert Formular und Vorschau.
- Texteingaben aktualisieren Vorschau live.
- Ein manueller Zeilenumbruch wird korrekt dargestellt.
- Langer Text wird automatisch verkleinert.
- Unmöglich langer Text erzeugt sichtbare Overflow-Warnung.
- Text-Override kann gesetzt und zurückgesetzt werden.
- Hintergrundwechsel funktioniert.
- Zoom/X/Y des Hintergrunds funktionieren.

## Upload

- gültiges JPG erfolgreich
- gültiges PNG erfolgreich
- gültiges WebP erfolgreich
- falsche Dateiendung mit Nicht-Bildinhalt wird abgelehnt
- zu große Datei wird abgelehnt
- Dateiname mit Sonderzeichen/Traversal-Versuch kann nicht aus dem Zielordner ausbrechen
- neu hochgeladenes Bild erscheint ohne Seitenreload und wird ausgewählt

## Template-Editor

- neues leeres Template anlegen
- bestehendes duplizieren
- Text-, Shape-, Image- und Photo-Element hinzufügen
- Element verschieben und Größe ändern
- Rotation setzen
- Layerreihenfolge ändern
- Feld anlegen und Text daran binden
- speichern, Seite neu laden, identische Positionen/Eigenschaften wieder vorhanden
- Template löschen nur nach Bestätigung

## Export

- PNG 1×
- PNG 2×
- JPG 1×
- JPG 2×
- JPG-Qualitätsregler greift
- heruntergeladene Datei und serverseitige Archivdatei sind visuell identisch
- Dimensionen stimmen exakt
- Sidecar-Metadaten stimmen
- Dateinamenskollision überschreibt nichts

## Exportarchiv

- neuester Export erscheint oben
- Thumbnail sichtbar
- Ansehen funktioniert
- Download funktioniert
- Suche nach Dateinamen funktioniert

## Logging

In `docker compose logs web` müssen sinnvolle Einzeiler erscheinen für:

- Background upload success/reject
- template create/update/duplicate/delete
- export success/failure
- validation errors

Jede relevante Zeile enthält Request-ID.

## Browser

Ziel: aktuelle Desktop-Versionen von Chrome/Edge/Firefox und Safari soweit ohne Spezialcode erreichbar. Primärer Testbrowser darf Chromium sein.

Keine unerwarteten Console Errors im normalen Workflow.

## Definition of Done

Das Projekt ist erst fertig, wenn Codex mindestens einen echten End-to-End-Durchlauf durchgeführt hat:

`Template laden → Texte ändern → Background wählen/uploaden → Exportieren → Datei im Archiv prüfen → erneut herunterladen`.
