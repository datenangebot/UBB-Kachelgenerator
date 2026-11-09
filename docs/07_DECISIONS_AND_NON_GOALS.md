# 07 – Architekturentscheidungen und Non-Goals

## Fest entschieden

- PHP + HTML + CSS + Vanilla JS
- Bootstrap 5 lokal vendort
- kein Build-Prozess
- keine Datenbank
- lokale Entwicklung via Docker/PHP 8.3 Apache
- Produktion auf normalem Plesk-PHP-Webspace
- Basic Auth außerhalb der Anwendung
- Templates als JSON-Dateien
- Backgrounds und Exporte als Dateien
- Export clientseitig aus dem Preview-DOM
- Exportkopie immer serverseitig speichern
- ausführliches PHP-Logging via `error_log()`
- Desktop-first

## Bewusste Non-Goals für v1

Nicht implementieren:

- Benutzerverwaltung, Login, Rollen
- Datenbank
- Social-Media-Posting
- n8n-Anbindung
- Termin-/Kalenderintegration
- freies Vektorzeichnen
- Pfade/Bezier
- komplexe Bildfilter
- Ebenengruppen
- Animationen
- Kollaboration/Mehrbenutzer-Locking
- Undo-Historie über viele Schritte (nur der letzte Bearbeitungsschritt ist rückgängig machbar)
- Export löschen
- Template-Versionshistorie
- Cloudspeicher
- responsive Smartphone-Bearbeitung
- vollständiger Canva-/Photoshop-Ersatz

## Später denkbar, aber nicht vorwegnehmen

- Social-Media-Zielgrößen
- mehrere Exportgrößen in einem Batch
- n8n-Webhook nach Export
- Template-Versionshistorie
- zusätzliche Feldtypen (Datum, Auswahl etc.)

Diese Punkte sollen die Architektur nicht unnötig komplizieren. Nur einfache Erweiterbarkeit berücksichtigen.

## Ergänzungen nach v1

- Einstufiges Rückgängig im Template-Editor; Eingaben und Ziehbewegungen werden jeweils zusammengefasst. Speicherstatus und Warnung vor dem Verwerfen ungespeicherter Änderungen bei Navigation, Neuladen und Schließen.

- Logo-/Asset-Upload im Template-Editor, auch für ersetzbare Standardfotos.
- Neue Exporte mit versioniertem Generatorzustand und vollständiger Template-Kopie erneut öffnen. Alte Exporte bleiben unverändert und ohne Ladefunktion.
- Clientseitiger PDF-Export: Rasterebenen für Bildmaterial und Flächen, echte Texte mit lokal eingebetteten Schrift-Teilmengen. Derselbe lokale Schriftkatalog versorgt Vorschau, PNG/JPG und PDF; keine zusätzliche Server-Laufzeit oder Datenbank.
