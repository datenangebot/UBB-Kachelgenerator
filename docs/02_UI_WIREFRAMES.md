# 02 – UI-Wireframes (textuelle Schemata)

Die Schemata definieren Informationsarchitektur und Bedienlogik, nicht pixelgenaues Styling.

## 1. Hauptansicht – Generator

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ UBB Kachelgenerator                     [ Templates ] [ Bisherige Exporte ]                     │
├────────────────────────┬───────────────────────────────────────────────┬─────────────────────────┤
│ INHALT                 │                                               │ DESIGN                  │
│                        │                                               │                         │
│ Überschrift        ⚙   │                                               │ Template                │
│ ┌────────────────────┐ │                                               │ [ Standard Magenta ▼ ]  │
│ │150 Jahre           │ │                                               │                         │
│ │Neuwittenbek        │ │                LIVE-VORSCHAU                  │ Hintergrund             │
│ └────────────────────┘ │                                               │                         │
│                        │            ┌──────────────────────┐           │ ┌────┐ ┌────┐ ┌────┐   │
│ Datum              ⚙   │            │                      │           │ │    │ │ ✓  │ │    │   │
│ [ Sa 29.08.          ] │            │                      │           │ └────┘ └────┘ └────┘   │
│                        │            │       KACHEL         │           │                         │
│ Uhrzeit            ⚙   │            │                      │           │ [ Alle Bilder … ]      │
│ [ 18:00h             ] │            │                      │           │ [ + Bild hochladen ]   │
│                        │            │                      │           │                         │
│ Haupttext          ⚙   │            └──────────────────────┘           │ Bild                    │
│ [ Uni-BigBand Kiel   ] │                                               │ Zoom  ─────●─────       │
│                        │                 [ − ] 100 % [ + ]              │ X     ─────●─────       │
│ Seitentext         ⚙   │                                               │ Y     ───────●───       │
│ [ Summer · Swing ... ] │                                               │ [ Zentrieren ]          │
│                        │                                               │                         │
│                        │                                               │ □ Hilfslinien anzeigen  │
├────────────────────────┴───────────────────────────────────────────────┴─────────────────────────┤
│ [ Zurücksetzen ]                                          [ Exportieren … ]                     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Das Zahnrad/Feinjustierungssymbol eines Textfeldes öffnet ein kleines Modal oder Popover für Overrides.

## 2. Text-Feinjustierung

```text
┌────────────────────────────────────────────┐
│ Haupttext – Feinjustierung              × │
├────────────────────────────────────────────┤
│ Schriftgröße                              │
│ ● Automatisch                             │
│ ○ Manuell            [ 72 ] px            │
│                                            │
│ X-Offset             [ 0 ] px             │
│ Y-Offset             [ 0 ] px             │
│                                            │
│ Templatebereich                            │
│ Max: 72 px · Min: 46 px · max. 2 Zeilen   │
│                                            │
│ [ Auf Templatewerte zurücksetzen ]        │
└────────────────────────────────────────────┘
```

## 3. Hintergrundgalerie

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Hintergrundbild auswählen                                                × │
├──────────────────────────────────────────────────────────────────────────────┤
│ Suche [____________________________]          [ + Neues Bild hochladen ]     │
│                                                                              │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │             │  │             │  │             │  │             │          │
│ │   Konzert   │  │   Konzert   │  │   Bühne     │  │   Bandfoto  │          │
│ │     01      │  │     02      │  │     03      │  │     04      │          │
│ │             │  │             │  │             │  │             │          │
│ └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
│ konzert01.jpg    konzert02.jpg    stage23.jpg      band2025.jpg             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 4. Hintergrund-Upload

```text
┌──────────────────────────────────────────────────┐
│ Neues Hintergrundbild                        × │
├──────────────────────────────────────────────────┤
│                                                  │
│      ┌────────────────────────────────────┐      │
│      │                                    │      │
│      │   Bild hier hineinziehen           │      │
│      │                                    │      │
│      │          oder                      │      │
│      │                                    │      │
│      │      [ Datei auswählen ]           │      │
│      │                                    │      │
│      └────────────────────────────────────┘      │
│                                                  │
│ JPG · PNG · WebP · max. 20 MB                    │
│                                                  │
│                           [ Abbrechen ] [ Upload ]│
└──────────────────────────────────────────────────┘
```

Nach Erfolg: Modal schließen, Liste aktualisieren, Datei auswählen, Toast `Upload erfolgreich`.

## 5. Template-Übersicht

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Templates                                        [ + Neues Template ]         │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                  │
│ │                 │ │                 │ │                 │                  │
│ │    Vorschau     │ │    Vorschau     │ │    Vorschau     │                  │
│ │                 │ │                 │ │                 │                  │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘                  │
│ Standard Magenta   Vollbild Konzert    Sommer                                │
│                                                                               │
│ [ Bearbeiten ]     [ Bearbeiten ]      [ Bearbeiten ]                        │
│ [ Duplizieren ]    [ Duplizieren ]     [ Duplizieren ]                       │
│ [ Löschen ]        [ Löschen ]         [ Löschen ]                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 6. Neues Template

```text
┌───────────────────────────────────────────────┐
│ Neues Template                            × │
├───────────────────────────────────────────────┤
│ Name                                          │
│ [ Weihnachtskonzert 2027                  ] │
│                                               │
│ Grundlage                                     │
│ ● Leeres Template                             │
│ ○ Standard Magenta                            │
│ ○ Vollbild Konzert                            │
│                                               │
│ Größe                                         │
│ Breite    [ 1138 ] px                         │
│ Höhe      [ 1138 ] px                         │
│                                               │
│                      [ Abbrechen ] [ Anlegen ] │
└───────────────────────────────────────────────┘
```

## 7. Template-Editor

Links zwei Tabs: `Elemente` und `Felder`.

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Template: Standard Magenta                [ Vorschau ] [ Speichern ] [ Speichern als … ]       │
├───────────────────────┬────────────────────────────────────────────────┬────────────────────────┤
│ [Elemente] [Felder]   │                                                │ EIGENSCHAFTEN          │
│                       │                                                │                        │
│ ☰ Hintergrundfoto     │                                                │ Element                │
│ ☰ Magenta Fläche      │                                                │ Haupttext              │
│ ☰ Überschrift         │                                                │                        │
│ ☰ Datum               │                                                │ Position / Größe       │
│ ☰ Uhrzeit             │            TEMPLATE-CANVAS                     │ X       [ 186 ]        │
│ ☰ Haupttext           │                                                │ Y       [ 288 ]        │
│ ☰ Seitentext          │           ┌─────────────────────┐              │ Breite  [ 720 ]        │
│ ☰ Logo                │           │                     │              │ Höhe    [ 100 ]        │
│                       │           │    ┌──────────┐     │              │ Rotation[   0 ] °     │
│ [+ Text]              │           │    │ Auswahl  │     │              │                        │
│ [+ Fläche]            │           │    └──────────┘     │              │ Text                   │
│ [+ Bild]              │           │                     │              │ Schrift [ Fallback ▼ ] │
│ [+ Foto]              │           └─────────────────────┘              │ Größe   [ Auto ▼ ]     │
│                       │                                                │ Gewicht [ Bold ▼ ]     │
│ [↑] [↓] Ebene         │           Zoom  [−] 75 % [+]                    │ Farbe   [ #ffffff ]    │
│                       │                                                │                        │
│                       │                                                │ Autofit                │
│                       │                                                │ ☑ Text verkleinern      │
│                       │                                                │ Min. Größe [ 46 ]       │
│                       │                                                │ Max. Zeilen [ 2 ]       │
│                       │                                                │                        │
│                       │                                                │ [ Element löschen ]     │
└───────────────────────┴────────────────────────────────────────────────┴────────────────────────┘
```

### Felder-Tab

```text
┌─────────────────────────────┐
│ FELDER                      │
│                             │
│ ☰ Überschrift               │
│ ☰ Datum                     │
│ ☰ Uhrzeit                   │
│ ☰ Haupttext                 │
│ ☰ Seitentext                │
│                             │
│ [ + Feld hinzufügen ]       │
└─────────────────────────────┘
```

Feldeigenschaften rechts:

```text
ID             [ headline       ]
Bezeichnung    [ Überschrift    ]
Eingabetyp     [ Mehrzeilig  ▼ ]
Standardwert   [                ]
Sortierung     [ 10             ]
```

## 8. Exportmodal

```text
┌──────────────────────────────────────────────────┐
│ Kachel exportieren                           × │
├──────────────────────────────────────────────────┤
│ Dateiname                                       │
│ [ UBB_Neuwittenbek_2026                     ] │
│                                                  │
│ Format                                          │
│ ● PNG                                            │
│ ○ JPG                                            │
│                                                  │
│ Auflösung                                       │
│ ● 1×       1138 × 1138                         │
│ ○ 2×       2276 × 2276                         │
│                                                  │
│ JPG-Qualität                                    │
│ ─────────────●────  90 %                         │
│ (nur bei JPG aktiv)                              │
│                                                  │
│ Hinweis: Eine Kopie wird im Archiv gespeichert. │
│                                                  │
│                  [ Abbrechen ] [ Exportieren ]   │
└──────────────────────────────────────────────────┘
```

## 9. Exportergebnis

```text
┌───────────────────────────────────────────────┐
│ ✓ Export erfolgreich                         │
│                                               │
│ UBB_Neuwittenbek_2026.png                    │
│ 1138 × 1138 · PNG                            │
│                                               │
│ [ Herunterladen ] [ Archiv öffnen ] [ Schließen ]
└───────────────────────────────────────────────┘
```

## 10. Exportarchiv

```text
┌────────────────────────────────────────────────────────────────────────────────────┐
│ Bisherige Exporte                                               [ Suche ________ ] │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────┐  UBB_2026-08-29_Neuwittenbek.png                                 │
│ │              │  29.08.2026 · 17:42                                              │
│ │   Vorschau   │  Template: Standard Magenta                                      │
│ │              │  1138 × 1138 · PNG                                               │
│ └──────────────┘  [ Ansehen ] [ Herunterladen ]                                    │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────┐  UBB_2026-07-17_Sommerkonzert.jpg                                │
│ │              │  17.07.2026 · 14:21                                              │
│ │   Vorschau   │  Template: Vollbild                                               │
│ │              │  2276 × 2276 · JPG                                               │
│ └──────────────┘  [ Ansehen ] [ Herunterladen ]                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```
