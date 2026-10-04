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

Bindet das global im Generator gewählte Hintergrundfoto ein.

Eigenschaften:

- id, name, type=`photo`
- x, y, width, height
- rotation
- opacity
- zIndex
- crop defaults: `positionX`, `positionY`, `zoom`
- `objectFit` in v1 fest `cover`

Der Generator speichert Photo-Overrides pro aktuellem Entwurf: gewählte Datei, positionX/Y, zoom.

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
