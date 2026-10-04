# UBB Kachelgenerator – Codex Handoff

Dieses Paket beschreibt die gewünschte Anwendung vollständig genug, damit Codex das Projekt lokal unter Docker entwickeln, testen und anschließend auf einen normalen PHP-Webspace/Plesk deploybar machen kann.

## Empfohlene Verwendung

1. Lege das Projekt unter `/Users/SteffeFl/Documents/Dev/ubb-kachelgenerator` an.
2. Lege den Inhalt dieses Handoff-Pakets zunächst in einem Unterordner `docs/handoff/` des Projekts ab oder gib Codex den Ordner als Referenz.
3. Starte Codex mit `CODEX_MASTER_PROMPT.md`.
4. Codex soll zuerst alle Dokumente lesen, dann implementieren und fortlaufend im Docker-Container testen.

## Dokumente

- `CODEX_MASTER_PROMPT.md` – ausführlicher Arbeitsauftrag für Codex
- `docs/01_PRODUCT_SPEC.md` – Produktumfang und Nutzerabläufe
- `docs/02_UI_WIREFRAMES.md` – textuelle UI-Schemata
- `docs/03_TEMPLATE_MODEL.md` – Datenmodell für Templates und Elemente
- `docs/04_API_AND_STORAGE.md` – PHP-API, Verzeichnisse und Persistenz
- `docs/05_TEST_ACCEPTANCE.md` – Testplan und Abnahmekriterien
- `docs/06_DEPLOYMENT_LOGGING_SECURITY.md` – Docker-Entwicklung, Plesk, Logging, Upload-Sicherheit
- `docs/07_DECISIONS_AND_NON_GOALS.md` – feste Architekturentscheidungen und bewusst ausgeschlossene Funktionen
- `docs/template.example.json` – Beispiel für ein Template
- `docs/export-metadata.example.json` – Beispiel für Export-Metadaten
- `reference/UBB-150-J-Neuwittenbek_v1.png` – bestehende Werbekachel als visuelle Referenz (1138 × 1138 px)

## Wichtig

Das Referenzbild ist eine Layout-Referenz. Es darf nicht als einzige fertig gerenderte Hintergrundgrafik missbraucht werden. Das Ziel ist ein echtes, editierbares Template mit getrennten Text-, Bild-, Foto- und Flächenelementen.
