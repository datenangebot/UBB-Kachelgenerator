# 01 – Produktspezifikation

## Zweck

Der UBB Kachelgenerator ist ein internes Werkzeug zur Erstellung wiederkehrender Werbekacheln für Auftritte einer Big Band. Wiederkehrende Layoutarbeit soll automatisiert werden, ohne die Möglichkeit zu verlieren, Inhalte und einzelne Darstellungsdetails anzupassen.

## Rollen

In v1 gibt es keine Rollen-/Benutzerverwaltung. Zugriffsschutz erfolgt vollständig über HTTP Basic Auth des Webspaces/Plesk.

## Hauptbereiche

### A. Kachelgenerator

Der Benutzer wählt ein Template, trägt Inhalte ein, wählt ein vorhandenes Hintergrundfoto oder lädt eines hoch und sieht jede Änderung sofort in der zentralen Vorschau.

Layout:

- links: Inhalt/Felder
- Mitte: Live-Kachel
- rechts: Design/Template/Hintergrund/Feinjustierung
- unten: Zurücksetzen und Exportieren

Die Formularfelder links werden aus `template.fields` erzeugt. Templates dürfen unterschiedliche Felder haben.

### B. Hintergrundbibliothek

Alle Dateien eines definierten Background-Ordners stehen zur Auswahl. Rechts werden einige Thumbnails angezeigt. Eine vollständige Galerie öffnet sich in einem Modal. Uploads werden direkt in diese Bibliothek übernommen und nach Erfolg ausgewählt.

### C. Template-Verwaltung

Vorhandene Templates werden als Karten mit Preview/Name angeboten. Aktionen:

- bearbeiten
- duplizieren
- löschen mit Bestätigung
- neues Template

### D. Template-Editor

Ein reduzierter Layouteditor, kein Voll-Grafikprogramm.

Elemente:

- Photo
- Text
- Shape/Rechteck
- Image/Logo

Funktionen:

- Element wählen
- verschieben
- Größe ändern
- Rotation numerisch, optional grafischer Handle wenn unkompliziert
- Ebenenreihenfolge ändern
- Eigenschaften numerisch und über Controls bearbeiten
- dynamische Textfelder definieren/binden
- Canvasgröße festlegen
- speichern / speichern als / duplizieren

### E. Export

Exportmodal:

- Dateiname, editierbar
- PNG oder JPG
- 1× oder 2×
- JPG-Qualität nur bei JPG
- serverseitige Archivkopie ist immer aktiv und nicht optional

Der Export wird aus demselben DOM erzeugt wie die Live-Vorschau. Nach erfolgreicher serverseitiger Speicherung wird die Datei zum Browser-Download angeboten.

### F. Exportarchiv

Ansicht der bisherigen Exporte:

- Thumbnail
- Dateiname
- Datum/Uhrzeit
- verwendetes Template
- Abmessungen/Format
- Ansehen
- Herunterladen
- Suche nach Dateiname

Keine Löschfunktion in v1.

## Verhalten von Text

Ein Text-Element besitzt eine feste Layoutbox. In Auto-Modus wird zwischen `maxFontSize` und `minFontSize` so groß wie möglich gerendert, ohne Box oder `maxLines` zu überschreiten.

Der Benutzer soll im Generator nicht jedes Mal manuell positionieren müssen. Manuelle Feinjustierung ist nur als begrenzter Override vorgesehen:

- Schriftgröße Auto oder manuell
- X-Offset
- Y-Offset
- Reset

Manuelle Zeilenumbrüche im Text werden respektiert.

Wenn Text bei minimaler Schriftgröße nicht passt, muss eine sichtbare Warnung erscheinen. Kein stilles Abschneiden.

## Hintergrundfoto

Das Template besitzt ein `photo`-Element, das das gewählte Bild rendert. Der Benutzer kann:

- Bild auswählen
- neues Bild hochladen
- X/Y-Bildposition verschieben
- Zoom verändern
- zentrieren/resetten

Der Bildausschnitt darf direkt in der Vorschau per Drag verändert werden, wenn dies ohne Konflikt mit Textelementen umsetzbar ist. Alternativ/zusätzlich stehen Slider zur Verfügung.

## Dateigrößen und Formate

Upload in v1:

- JPG/JPEG
- PNG
- WebP
- Default-Limit 20 MB, zentral konfigurierbar

Export:

- PNG
- JPG

## Referenztemplate

`standard-magenta`, 1138 × 1138 px, angelehnt an `reference/UBB-150-J-Neuwittenbek_v1.png`.

Die genaue Hausschrift und ein separates Originallogo sind nicht Teil des Handoffs. Nicht erfinden; Fallback/Platzhalter sauber kennzeichnen.
