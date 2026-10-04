# 06 – Deployment, Logging und Sicherheit

## Development via Docker

Minimalziel:

```yaml
services:
  web:
    image: php:8.3-apache
    ports:
      - "8080:80"
    volumes:
      - ./:/var/www/html
```

Keine zusätzliche Laufzeitkomponente einführen, sofern nicht notwendig.

## Produktion/Plesk

Deployment soll im Wesentlichen sein:

1. Projektdateien in Webspace kopieren.
2. PHP 8.2+ auswählen.
3. Schreibrechte für `storage/backgrounds`, `storage/templates`, `storage/exports` setzen.
4. Basic Auth für das gesamte Anwendungsverzeichnis in Plesk aktivieren.
5. Anwendung aufrufen.

README muss konkrete Hinweise für Dateirechte enthalten, ohne pauschal `777` zu empfehlen.

## Logging

Primäres Ziel: Plesk Domain Logs.

PHP-Logger zentral kapseln, intern aber letztlich `error_log()` verwenden.

Format:

```text
[UBB-KACHEL] level=INFO request_id=A1B2C3 user=tom action=template.save template=standard-magenta result=ok
```

Felder nach Bedarf:

- level
- request_id
- user
- action
- template
- filename
- size
- format
- width/height
- duration_ms
- error_code

Werte so escapen/normalisieren, dass pro Event exakt eine Logzeile entsteht.

## Request-ID

Pro API-Request erzeugen, z. B. 6–10 zufällige hex/URL-safe Zeichen. In Response zurückgeben und in allen Logzeilen desselben Requests verwenden.

## Basic-Auth-Benutzer

Wenn Apache/Plesk `REMOTE_USER` setzt, diesen Wert loggen. Keine eigene Authentifizierung implementieren.

## Upload-Sicherheit

- `UPLOAD_ERR_*` prüfen
- Maximalgröße serverseitig prüfen
- `finfo` MIME prüfen
- `getimagesize`/äquivalente echte Bildprüfung
- nur JPEG/PNG/WebP
- serverseitig neuen sicheren Dateinamen bestimmen
- keine Originalpfade vertrauen
- keine ausführbaren Endungen
- niemals Client-MIME vertrauen

## Template-Sicherheit

- JSON-Größe begrenzen
- JSON parse errors sauber melden
- IDs und Assetpfade validieren
- nur Whitelist-Eigenschaften/Typen akzeptieren oder unbekannte Felder kontrolliert ignorieren
- Text niemals über `innerHTML` einsetzen; `textContent`/DOM APIs verwenden

## CSRF

Auch hinter Basic Auth für schreibende PHP-Endpunkte einen einfachen Session-CSRF-Token verwenden. Frontend holt/erhält Token beim initialen Page Load und sendet ihn als Header oder Form-Feld.

## Webserver-Schutz

Falls sensible JSON-/Hilfsdateien im Document Root liegen, per `.htaccess` direkten Zugriff blockieren. Export- und Background-Dateien dürfen über definierte URLs erreichbar sein, weil die gesamte Anwendung ohnehin durch Basic Auth geschützt ist.

## Backups

README soll darauf hinweisen, dass für vollständige Sicherung mindestens folgende Verzeichnisse kopiert werden müssen:

- `storage/backgrounds`
- `storage/templates`
- `storage/exports`
- ggf. nachträglich ergänzte Fonts/Logos/Template-Assets
