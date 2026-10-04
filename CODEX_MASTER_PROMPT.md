# Master-Prompt für Codex: UBB Kachelgenerator

Baue eine kleine interne Webanwendung namens **UBB Kachelgenerator**. Sie dient einer Big Band zur schnellen Erstellung quadratischer Werbekacheln für Auftritte. Eine bestehende Kachel liegt als visuelle Referenz unter `reference/UBB-150-J-Neuwittenbek_v1.png` vor. Sie ist 1138 × 1138 px.

## Arbeitsweise

Lies vor dem Programmieren vollständig:

- `docs/01_PRODUCT_SPEC.md`
- `docs/02_UI_WIREFRAMES.md`
- `docs/03_TEMPLATE_MODEL.md`
- `docs/04_API_AND_STORAGE.md`
- `docs/05_TEST_ACCEPTANCE.md`
- `docs/06_DEPLOYMENT_LOGGING_SECURITY.md`
- `docs/07_DECISIONS_AND_NON_GOALS.md`

Behandle diese Dokumente als Spezifikation. Wenn eine Kleinigkeit nicht festgelegt ist, entscheide pragmatisch für die schlankste, wartbarste Lösung und dokumentiere die Entscheidung im README. Erfinde keine unnötigen Features.

## Zielumgebung

Erstelle das Projekt unter:

`/Users/SteffeFl/Documents/Dev/ubb-kachelgenerator`

Der Benutzer hat lokal kein PHP installiert, aber Docker Desktop ist vorhanden und Codex darf Docker starten. Das Projektverzeichnis darf als Bind-Mount verwendet werden.

### Lokale Entwicklung

Verwende eine minimale `compose.yaml` mit `php:8.3-apache`. Die Anwendung soll danach unter `http://localhost:8080` erreichbar sein. Quellcodeänderungen müssen durch den Bind-Mount ohne Image-Rebuild sichtbar werden.

### Produktion

Die Anwendung muss unverändert auf einem üblichen Plesk-/Apache-PHP-Webspace lauffähig sein. Docker ist dort **nicht** erforderlich. Die komplette Anwendung muss ohne Shell-Daemon, Queue, Node.js, Datenbank oder serverseitigen Headless-Browser funktionieren.

## Technischer Rahmen – verbindlich

- PHP 8.2+; lokale Referenzumgebung PHP 8.3 + Apache.
- HTML5, CSS, Vanilla JavaScript.
- Bootstrap 5.x für die Anwendungsoberfläche; lokal im Repository unter `assets/vendor/`, kein CDN.
- Kein npm, kein yarn, kein pnpm, kein Vite, kein Webpack, kein sonstiger Build-/Compile-Schritt.
- Kein JavaScript-Framework wie React/Vue/Svelte.
- Keine Datenbank.
- Kein Composer, solange er nicht zwingend erforderlich ist. Bevor Composer eingeführt wird, zuerst eine Lösung ohne Composer wählen.
- Kleine Browserbibliotheken sind erlaubt, wenn sie direkt als fertige JS/CSS-Datei lokal vendort werden können. Quellen/Lizenzen in `THIRD_PARTY.md` dokumentieren.
- Die Kachel selbst wird nicht mit Bootstrap gestaltet. Bootstrap ist nur für das UI der Anwendung gedacht. Der Renderer verwendet eigenes CSS/DOM.
- Authentifizierung ist nicht Teil der Anwendung. Der produktive Webspace schützt das gesamte Verzeichnis per HTTP Basic Auth.

## Hauptfunktionen

Implementiere drei Hauptbereiche:

1. **Kachelgenerator**
   - Links: dynamisches Inhaltsformular, aus dem gewählten Template erzeugt.
   - Mitte: Live-Vorschau der Kachel.
   - Rechts: Templatewahl, Hintergrundbildwahl, Upload, Bildausschnitt und Feineinstellungen.
   - Jede Texteingabe aktualisiert die Vorschau sofort.
   - Hintergrundbild kann verschoben und gezoomt werden.
   - Text wird innerhalb seiner definierten Box automatisch verkleinert und umgebrochen.
   - Wenn Text selbst bei Mindestschriftgröße nicht passt, sichtbar warnen statt still abzuschneiden.
   - Optional pro Text-Element eine begrenzte manuelle Feinjustierung: Auto/Manuell für Schriftgröße sowie X-/Y-Offset; Reset auf Templatewerte.

2. **Template-Verwaltung und Template-Editor**
   - Templates auflisten, neu anlegen, duplizieren, bearbeiten, löschen (mit Bestätigung).
   - Templates liegen als JSON-Dateien auf dem Dateisystem.
   - Keine fest verdrahteten Formularfelder: Ein Template definiert seine Felder und Elemente.
   - Editor mit Ebenen-/Elementliste links, Canvas in der Mitte, Eigenschaften rechts.
   - Elemente auf dem Canvas per Maus verschieben und skalieren; numerische Eingabe für präzise Werte.
   - Ebenenreihenfolge änderbar.
   - Mindestens folgende Elementtypen in v1:
     - `photo`: dynamisches Veranstaltungs-/Hintergrundfoto, auswählbar im Generator, mit Crop/Zoom/Position.
     - `text`: statischer Text oder an ein Template-Feld gebundener Text.
     - `shape`: rechteckige Farbfläche mit Farbe, Deckkraft und optionalem Radius.
     - `image`: statisches Bild/Logo aus lokalen Template-Assets.
   - Gemeinsame Eigenschaften, soweit sinnvoll: x, y, width, height, rotation, opacity, z-order.
   - Text-Eigenschaften: Font, Gewicht, Größe/Auto-Fit, min/max Fontgröße, Zeilenhöhe, Farbe, Ausrichtung, maxLines, Wrap, letterSpacing.
   - Ein dynamisches Text-Element bindet an ein Feld aus `template.fields`; diese Felder bestimmen das linke Formular im Generator.
   - Canvasgröße pro Template frei konfigurierbar. Das erste Referenztemplate verwendet 1138 × 1138 px.
   - `Speichern`, `Speichern als…`, `Duplizieren`.

3. **Export und Exportarchiv**
   - Exportmodal mit Dateiname, Format PNG/JPG, 1× oder 2× Auflösung; bei JPG Qualitätsregler.
   - Jede Exportdatei wird immer zusätzlich serverseitig archiviert.
   - Export erfolgt clientseitig aus exakt derselben DOM-Darstellung wie die Vorschau. Keine zweite, abweichende Renderlogik auf dem Server.
   - Das erzeugte Blob wird an PHP geschickt, serverseitig validiert und gespeichert; danach wird der Download im Browser angeboten.
   - Exportarchiv im Frontend: Vorschaubild, Dateiname, Erstellungszeit, Template, Abmessungen, Download/Ansehen.
   - Keine Löschfunktion für Exporte in v1.
   - Zu jedem Export eine JSON-Sidecar-Datei mit Metadaten speichern.

## Hintergrundbilder

- Alle verfügbaren Hintergrundbilder werden aus einem festgelegten, beschreibbaren Ordner gelesen.
- Direkt in der rechten Seitenleiste einige Thumbnails anzeigen; `Alle Bilder…` öffnet eine Galerie im Bootstrap-Modal.
- Suche/Filter in der Galerie nach Dateiname.
- `+ Bild hochladen` öffnet ein Modal mit Drag&Drop und Dateiauswahl.
- Erlaubte Uploads: JPG/JPEG, PNG, WebP.
- MIME und tatsächliches Bild serverseitig prüfen, nicht nur Dateiendung.
- Dateinamen sicher normalisieren; Kollisionen ohne Überschreiben auflösen.
- Nach erfolgreichem Upload Galerie aktualisieren, Modal schließen und neues Bild direkt auswählen.

## Rendering und Text-Fit

Die Vorschau muss WYSIWYG zum Export sein. Verwende für Vorschau und Export denselben Render-DOM.

Für automatisch skalierte Texte:

1. Beginne bei `maxFontSize`.
2. Miss reale Breite/Höhe im Browser.
3. Reduziere effizient, vorzugsweise per binärer Suche, bis der Inhalt in die definierte Box und `maxLines` passt oder `minFontSize` erreicht ist.
4. Manuelle Zeilenumbrüche aus dem Text müssen erhalten bleiben.
5. Wenn bei `minFontSize` weiterhin Overflow besteht, Element im Generator sichtbar als problematisch markieren und eine verständliche Warnung anzeigen.
6. Die Berechnung muss nach Texteingabe, Templatewechsel, Font-Ladevorgang und Größenänderung zuverlässig erneut erfolgen.

Lokale Schriften müssen vor Messung und Export vollständig geladen sein (`document.fonts.ready`).

## Export-Technik

Wähle eine kleine browserseitige DOM→PNG/JPG-Lösung, die ohne Build-Prozess als lokale Vendor-Datei funktioniert und lokale Bilder/Fonts korrekt rendert. Bevorzuge eine etablierte, kleine Bibliothek. Dokumentiere Bibliothek, Version, Quelle und Lizenz in `THIRD_PARTY.md`.

Wichtig:

- Keine externen CDN-Abhängigkeiten.
- Keine serverseitige Browserautomation.
- Kein ImageMagick-Zwang.
- Export muss auch mit 2× Auflösung funktionieren.
- Zeige während des Exports einen Busy-State und verständliche Fehlermeldungen.
- Bei serverseitigem Archivierungsfehler gilt der Export als fehlgeschlagen; optional darf ein lokaler Download als Fallback angeboten werden, aber der Fehler muss klar sichtbar sein.

## Dateisystem statt Datenbank

Verwende JSON und Dateien mit atomarem Schreiben (`temp` + `rename`, wo möglich, plus geeignete Sperre) für schreibende Vorgänge.

Vorgeschlagene Struktur:

```text
ubb-kachelgenerator/
├── index.php
├── templates.php
├── exports.php
├── api/
├── lib/
├── assets/
│   ├── css/
│   ├── js/
│   ├── vendor/
│   ├── fonts/
│   ├── logos/
│   └── template-assets/
├── storage/
│   ├── backgrounds/
│   ├── templates/
│   └── exports/
├── docs/
├── tests/
├── compose.yaml
├── .htaccess
├── README.md
└── THIRD_PARTY.md
```

Passe Details an, wenn es technisch sinnvoll ist, aber halte die Trennung von statischen App-Assets und beschreibbaren Nutzdaten bei.

## PHP-API

Implementiere kleine JSON-Endpunkte, mindestens für:

- Backgrounds listen
- Background hochladen
- Templates listen
- Template laden
- Template speichern
- Template duplizieren
- Template löschen
- Export speichern
- Exporte listen

Schreibende Requests nur per POST. Verwende einen einfachen Session-basierten CSRF-Schutz für schreibende Requests. API-Fehler liefern konsistentes JSON mit `ok`, `error`, `message`, `requestId` und passendem HTTP-Status.

## Logging – sehr wichtig

Der Betreiber möchte Vorgänge direkt im Plesk-Domainprotokoll sehen. Daher alle relevanten serverseitigen Ereignisse über PHP `error_log()` als strukturierte Einzeiler ausgeben.

Beispiel:

```text
[UBB-KACHEL] level=INFO request_id=8F31A user=tom action=background.upload filename=konzert.jpg size=4819237
```

Jeder API-Request bekommt eine kurze Request-ID. Wenn `$_SERVER['REMOTE_USER']` durch Basic Auth gesetzt ist, in das Log übernehmen; ansonsten `user=-`.

Mindestens loggen:

- API request start/end bei schreibenden Aktionen
- Template angelegt/geändert/dupliziert/gelöscht
- Hintergrundupload erfolgreich/abgelehnt
- Export gestartet/erfolgreich/fehlgeschlagen
- Validierungsfehler
- Dateisystemfehler
- unerwartete Exceptions/Fehler

Keine Bild-Base64-Daten, kompletten JSON-Templates oder sonstige riesige Payloads loggen.

Frontend-Fehler, die für Diagnose wichtig sind, dürfen über einen kleinen optionalen Log-Endpunkt serverseitig protokolliert werden; nicht jede UI-Interaktion loggen.

## Sicherheit und Robustheit

- Basic Auth wird außerhalb der App konfiguriert.
- Trotzdem Uploads und Dateipfade strikt validieren.
- Keine vom Client gelieferten Pfade direkt verwenden.
- Kein Directory Traversal.
- Nur erlaubte Dateitypen und Größen.
- Sinnvolles Uploadlimit zentral konfigurierbar, Default 20 MB.
- Template-JSON serverseitig validieren.
- HTML aus Benutzereingaben niemals ungefiltert als HTML interpretieren; Text nur als Text rendern.
- Schreiboperationen müssen Fehler sauber behandeln und dürfen existierende Dateien nicht versehentlich beschädigen.

## UI

Verwende Bootstrap 5 für Layout, Formulare, Modals, Buttons, Toasts und Navigation. Die Anwendung ist Desktop-first, soll aber bei kleineren Laptopbreiten brauchbar bleiben. Kein Anspruch auf Smartphone-Editor in v1.

Die verbindlichen textuellen Wireframes stehen in `docs/02_UI_WIREFRAMES.md`.

## Initiales Template

Lege ein Template `standard-magenta` an, dessen Grundidee sich am Referenzbild orientiert:

- quadratisch, 1138 × 1138
- magentafarbene Gestaltung
- Foto-/Bildbereich
- große Überschrift
- Datum/Uhrzeit
- Haupttext/Bandname
- seitlicher Text mit Rotation
- Logo-/Bildbereich

Wichtig: Das Referenzbild nicht als fertige Gesamtgrafik hinterlegen. Die Bestandteile sollen echte Template-Elemente sein. Wenn ein separates Original-Logo oder exakte Hausschriften fehlen, verwende im initialen Template einen klaren Platzhalter bzw. einen neutralen Fallback und dokumentiere im README, welches Asset später ersetzt werden soll. Keine Logos erfinden.

## Tests und Definition of Done

Arbeite iterativ und teste tatsächlich lokal im Docker-Container. Vor Abschluss:

1. `docker compose up -d` muss funktionieren.
2. PHP-Syntaxprüfung aller PHP-Dateien muss grün sein.
3. API-Smoke-Tests müssen laufen.
4. Im Browser müssen Generator, Upload, Template-Editor und Exportarchiv funktionieren.
5. Erzeuge mindestens ein Testtemplate und einen echten Testexport.
6. Prüfe, dass PNG/JPG im Serverarchiv liegt und die Sidecar-Metadaten korrekt sind.
7. Prüfe 1× und 2× Export.
8. Teste einen zu langen Text und verifiziere Auto-Fit sowie Overflow-Warnung.
9. Teste Background-Upload mit gültiger und ungültiger Datei.
10. Teste Template speichern/neu laden/duplizieren.
11. Kontrolliere `docker compose logs web`, dass relevante Events im PHP/Apache-Log auftauchen.
12. Browserkonsole soll im normalen Workflow frei von unerwarteten Fehlern sein.
13. README muss lokale Entwicklung, Plesk-Deployment, Schreibrechte, Verzeichnisse und Backup-Hinweise erklären.

Nutze bei Bedarf eine vorhandene Browserautomation in deiner Umgebung zum Testen, aber füge dafür keine Node-/Build-Abhängigkeit zum eigentlichen Projekt hinzu.

## Nicht tun

- Keine Datenbank einführen.
- Kein Node/npm als Projektvoraussetzung einführen.
- Kein SPA-Framework einführen.
- Keine Benutzerverwaltung bauen.
- Keine Social-Media-API-Anbindung bauen.
- Kein Canva-/Photoshop-Vollklon bauen.
- Keine freien Filter-/Effektketten für Bilder in v1.
- Keine Export-Löschfunktion in v1.
- Keine unnötige Architektur mit Repository-/Service-Layern, wenn einfache PHP-Module ausreichen.

## Abschluss

Wenn die Anwendung fertig und getestet ist:

- Gib eine kurze Zusammenfassung der Implementierung.
- Liste die lokal ausgeführten Tests mit Ergebnis auf.
- Nenne offene Punkte ausschließlich, wenn wirklich externe Assets/Entscheidungen fehlen.
- Hinterlasse das Projekt startbereit unter `/Users/SteffeFl/Documents/Dev/ubb-kachelgenerator`.
