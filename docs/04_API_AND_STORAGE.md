# 04 – API und Storage

## Verzeichnisse

Empfohlen:

```text
storage/
├── backgrounds/
├── templates/
└── exports/
    └── YYYY/
        └── MM/
```

Statische, vom Entwickler ausgelieferte Assets:

```text
assets/
├── fonts/
├── logos/
├── template-assets/
└── vendor/
```

## API-Konvention

Alle Antworten JSON:

Erfolg:

```json
{
  "ok": true,
  "requestId": "A1B2C3",
  "data": {}
}
```

Fehler:

```json
{
  "ok": false,
  "requestId": "A1B2C3",
  "error": "VALIDATION_ERROR",
  "message": "Verständliche Fehlermeldung"
}
```

HTTP-Status passend setzen.

## Endpunkte – Mindestumfang

Namensgebung darf leicht abweichen, die Funktionalität ist verbindlich.

Die Implementierung verwendet `api/index.php?action=...`:

- `fonts.list`: lokaler Schriftkatalog mit Familien, Aliasnamen und Dateien/Schnitten.
- `assets.upload` (POST, CSRF, Multipart-Feld `image`): JPG/PNG/WebP bis 20 MB nach `assets/template-assets/`, Antwort mit `asset`, `width`, `height`. Bestehende Dateien werden nicht ersetzt.
- `assets.list`: rekursive Liste vorhandener, erlaubter Template-Bilder (JPG/PNG/WebP/SVG) mit `asset`, URL, Dateiname, Anzeigename, `addedAt` und optionalen Abmessungen. Verweise außerhalb des Asset-Verzeichnisses werden ausgeschlossen. Neue Uploads speichern Originalnamen und Hinzufügungszeit in `<bild>.json`; Altdateien verwenden ohne Migration ihren bisherigen Dateinamen und ihr Dateidatum. Die Bildbibliothek filtert und sortiert diese Liste im Browser.
- `exports.save` (POST, CSRF, Multipart): PNG/JPG im Feld `image`; bei PDF zusätzlich `document` (PDF) und `image` (PNG-Vorschau). `metadata` ist JSON. Die PDF-Seitengröße beträgt Exportbreite/-höhe × 0,75 Punkte. Die Anwendung erzeugt einseitige PDFs ohne Object Streams, damit der Server Typ, Seitenanzahl und Seitengröße kontrollieren kann.
- `exports.list`: Archivübersicht ohne große Generatorzustände; `canRestore` ist nur bei vollständigem, unterstütztem Zustand und vorhandenen Bilddateien wahr. `previewUrl` ist optional, alte Einträge verwenden `url` als Vorschau.
- `exports.get&id=...`: einzelner Export samt Zustand; 409 bei fehlendem/unvollständigem Zustand. Die archivierte Template-Kopie ist unabhängig vom aktuellen Template-Verzeichnis.

### GET `/api/backgrounds-list.php`

Liefert sichere Metadaten der verfügbaren Bilder: Dateiname, relative Browser-URL, Größe/Abmessungen wenn günstig ermittelbar, Änderungszeit.

### POST `/api/backgrounds-upload.php`

Multipart-Upload. Validiert MIME, Bildinhalt, Größe, sichere Benennung. Antwort mit neuem Eintrag.

### GET `/api/templates-list.php`

Liste der Templates mit ID, Name, Größe, updatedAt und ggf. Preview.

### GET `/api/templates-get.php?id=...`

Vollständiges Template.

### POST `/api/templates-save.php`

JSON. Erstellen oder aktualisieren. Serverseitige Schema-/Plausibilitätsvalidierung. Atomar schreiben.

### POST `/api/templates-duplicate.php`

Quelle + neuer Name/ID. Kopie als neue JSON-Datei.

### POST `/api/templates-delete.php`

Löschen nach validierter ID. UI muss bestätigen.

### POST `/api/export-save.php`

Multipart: Bildblob + Metadaten. Server prüft:

- erlaubtes Format
- tatsächliches Bild
- sinnvolle Dimensionen
- Dateigröße
- sicherer Dateiname

Speichert Bild und Sidecar-JSON.

### GET `/api/exports-list.php`

Scannt Sidecars, sortiert newest-first und liefert Archivdaten. Suche kann clientseitig erfolgen, solange Umfang klein bleibt.

## Export-Sidecar

Soll mindestens enthalten:

- id
- createdAt
- filename
- format
- width
- height
- templateId
- templateName
- optional für alte Exporte: `generatorState` mit Feldwerten, Background-Datei und Overrides
- neue Exporte: `generatorState.version: 2`, vollständige `template`-Kopie (Schema 1), `fields`, `photos` und `textOverrides`. `photos` bildet jede Foto-Element-ID auf `{background, positionX, positionY, zoom}` ab. `background` ist ein Dateiname aus `storage/backgrounds/` oder null für das jeweilige Template-Standardfoto. Keine Foto-Elemente bedeutet eine leere Zuordnung.
- weiterhin unterstützt: `generatorState.version: 1` mit `background` und `photo`. Beim Laden wird der gemeinsame Zustand im Browser für alle Foto-Elemente übernommen. Bestehende Sidecars bleiben unverändert.
- optional `previewUrl`: PNG-Vorschau für PDF, sonst identisch mit `url`

Neue Zustände werden serverseitig validiert. Der Client hält die gerenderte Kachel und ihre Metadaten während des Exports als gemeinsame Momentaufnahme fest. Die aktuelle Template-Datei ist beim Speichern eines Exports mit vollständiger Kopie nicht erforderlich. Unversionierte alte Metadaten bleiben unverändert und gelten nicht als wiederherstellbar. Ein erneuter Export schreibt eine neue Datei samt Sidecar; vorhandene Exporte werden nie aktualisiert. Bildreferenzen bleiben gültig, weil Template-Assets und Hintergrundbilder bei Template-Änderungen nicht gelöscht werden.

Version 2 verlangt genau einen gültigen Foto-Zustand für jedes Foto-Element und akzeptiert keine unbekannten oder fehlenden Foto-IDs. Dateireferenzen und Ausschnittgrenzen werden für jedes Foto geprüft. Die Auswahl im Generator selbst ist flüchtig; nur ein Export persistiert den gesamten Entwurf.

## Dateinamen

Benutzer darf Export-Dateinamen editieren. Serverseitig:

- Pfadanteile entfernen
- problematische Zeichen ersetzen
- nur sichere Basename-Zeichen zulassen
- korrekte Endung serverseitig setzen
- bei Kollision z. B. `-2`, `-3` ergänzen; nie still überschreiben

## Atomare Schreibvorgänge

Für JSON:

1. in temporäre Datei im selben Zielverzeichnis schreiben
2. optional `flock`
3. vollständig flushen/schließen
4. `rename` auf Ziel

Dadurch soll ein abgebrochener Request kein halbes Template erzeugen.
