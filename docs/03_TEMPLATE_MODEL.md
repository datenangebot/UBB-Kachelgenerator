# 03 – Template-Datenmodell

## Grundprinzip

Templates sind JSON-Dateien. Renderer, Generator und Template-Editor verwenden dasselbe Modell. Es gibt keine separate hartcodierte Darstellung pro Template.

## Template

Pflichtfelder:

- `schemaVersion`
- `id`
- `name`
- `width`
- `height`
- `fields[]`
- `elements[]`

Optionale Metadaten:

- `createdAt`
- `updatedAt`
- `description`
- `preview`

## Fields

Ein Field erzeugt einen Eingabewert im Generator.

Empfohlene Eigenschaften:

```json
{
  "id": "headline",
  "label": "Überschrift",
  "inputType": "textarea",
  "defaultValue": "",
  "order": 10
}
```

`inputType` in v1:

- `text`
- `textarea`

Mehr Typen erst später, falls wirklich notwendig.

## Element: photo

Bindet das für dieses Foto-Element im Generator gewählte Bild ein. Mehrere Foto-Elemente lassen sich unabhängig belegen und zuschneiden.

Eigenschaften:

- id, name, type=`photo`
- x, y, width, height
- rotation
- opacity
- zIndex
- crop defaults: `positionX`, `positionY`, `zoom`
- `objectFit` in v1 fest `cover`
- optional `asset`: Standardfoto unter `assets/template-assets/`, im Editor hochladbar. Ohne individuellen Override zeigt der Generator dieses Foto mit dem eigenen `crop`. Bildwahl und Upload ersetzen ausschließlich das gewählte Foto-Element. Fehlendes `asset` bleibt abwärtskompatibel.

Der Generator speichert Overrides nach Element-ID: `photos[id]` enthält `background` (Dateiname aus `storage/backgrounds/` oder null für das Template-Standardfoto), `positionX`, `positionY` und `zoom`. Alle Foto-Elemente werden gespeichert, auch solche ohne gewählte Datei. Exportzustände der Version 1 behalten ihre bisherige gemeinsame Bildwahl/Ausschnitt-Darstellung beim Laden; erst neue Exporte verwenden den Zustand der Version 2. Das Template-Schema bleibt bei Version 1.

## Element: text

Kann statisch oder dynamisch sein.

Dynamisch:

```json
"binding": { "type": "field", "fieldId": "headline" }
```

Statisch:

```json
"binding": { "type": "static", "text": "Uni-BigBand" }
```

Eigenschaften:

- x, y, width, height
- rotation, opacity, zIndex
- fontFamily
- fontWeight
- fontSize oder Auto-Fit-Konfiguration
- minFontSize
- maxFontSize
- lineHeight
- maxLines
- wrap
- color
- textAlign: left/center/right
- verticalAlign: top/middle/bottom
- letterSpacing

Optional für spätere Erweiterungen reservieren, aber nicht in v1 bauen: textShadow, stroke, rich text.

Optional seit Erweiterung des Editors: `naming: {"id":"auto","name":"auto"}`. Beide Werte dürfen unabhängig `auto` oder `manual` sein. Bei Auswahl einer Feldverknüpfung übernimmt der Editor für automatische Werte die Feld-ID bzw. Feldbezeichnung; Element-IDs bleiben durch einen nummerierten Zusatz eindeutig. Eine manuelle Bearbeitung setzt den jeweiligen Wert auf `manual`. Rückgängig stellt die Kennzeichnung mit wieder her. Die Angabe wird mit dem Template und Export-Snapshot gespeichert; Template-Schema 1 bleibt bestehen. Ältere Templates ohne Angabe bleiben lesbar und werden konservativ behandelt: Nur generische Text-ID-/Namensvorgaben gelten als automatisch. Das reine Öffnen verändert keine bestehenden Dateien.

## Element: shape

V1 nur Rechteck:

- x, y, width, height
- rotation, opacity, zIndex
- fillColor
- borderRadius

Kein freies SVG-Zeichnen in v1.

## Element: image

Statisches Template-Asset, z. B. Logo.

- asset path nur aus freigegebenem Template-Asset-Verzeichnis
- x, y, width, height
- rotation, opacity, zIndex
- objectFit: contain/cover

Keine externen URLs.

Bild- und Foto-Assets können im Editor als JPG/PNG/WebP hochgeladen werden (20 MB). Der Upload wird unter einem neuen eindeutigen Dateinamen abgelegt und anschließend über `asset` referenziert. Das Speichern des Templates bleibt ein eigener Schritt. Assetdateien bleiben auch nach Template-Änderung oder -Löschung erhalten, damit archivierte Zustände weiter funktionieren.

## Koordinaten

Alle Geometriedaten werden in nativen Template-Pixeln gespeichert. Die Bildschirmvorschau skaliert lediglich die gesamte Canvas visuell. Dadurch bleiben Layout und Export unabhängig von der Browsergröße.

## Rotation

Rotation in Grad um das Elementzentrum. Das ist wichtig für den vertikalen Seitentext des Referenzlayouts.

## Z-Order

`zIndex` muss eindeutig bzw. deterministisch sortierbar sein. Beim Umsortieren ggf. auf fortlaufende Werte normalisieren.

## Validierung

Serverseitig mindestens prüfen:

- ID nur `[a-z0-9][a-z0-9_-]*`
- Breite/Höhe sinnvolle positive Grenzen, z. B. 100–6000
- Elementtypen nur aus Whitelist
- Geometriewerte numerisch
- Fontgrößen positive Grenzen
- Field-IDs eindeutig
- Element-IDs eindeutig
- dynamische Bindings müssen auf vorhandene Field-ID zeigen
- Assetpfade dürfen kein `..` enthalten und müssen im erlaubten Assetbereich liegen

## Versionierung

`schemaVersion: 1` in v1. Renderer muss unbekannte zukünftige Versionsnummern mit verständlichem Fehler ablehnen statt falsch zu rendern.
