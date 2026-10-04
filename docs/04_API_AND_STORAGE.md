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
- optional: `generatorState` mit Feldwerten, Background-Datei und Overrides zur späteren Nachvollziehbarkeit

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
