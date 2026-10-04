<?php
declare(strict_types=1);
const ROOT = __DIR__ . '/..';
const MAX_IMAGE_BYTES = 20971520;
const MAX_TEMPLATE_BYTES = 1048576;
const MAX_EXPORT_BYTES = 83886080;
const ID_RX = '/^[a-z0-9][a-z0-9_-]*$/D';
function storage(string $part): string { return ROOT . '/storage/' . $part; }
function csrf(): string {
    if (session_status() !== PHP_SESSION_ACTIVE) session_start();
    return $_SESSION['csrf'] ??= bin2hex(random_bytes(24));
}
