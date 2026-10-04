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
- Undo-Historie über viele Schritte (ein einfacher Reset ist ausreichend)
- Export löschen
- Template-Versionshistorie
- Cloudspeicher
- responsive Smartphone-Bearbeitung
- vollständiger Canva-/Photoshop-Ersatz

## Später denkbar, aber nicht vorwegnehmen

- Social-Media-Zielgrößen
- mehrere Exportgrößen in einem Batch
- n8n-Webhook nach Export
- Export erneut als Entwurf öffnen
- Template-Versionshistorie
- zusätzliche Feldtypen (Datum, Auswahl etc.)
- Logo-/Asset-Upload im Template-Editor

Diese Punkte sollen die Architektur nicht unnötig komplizieren. Nur einfache Erweiterbarkeit berücksichtigen.
