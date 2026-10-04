<?php
declare(strict_types=1);
require_once __DIR__ . '/config.php';
$requestId = strtoupper(bin2hex(random_bytes(4)));
function event_log(string $level, string $action, array $fields = []): void {
    global $requestId;
    $clean=fn($v)=>preg_replace('/[^\pL\pN._@-]+/u', '_', (string)$v) ?: '-';
    $parts = ['level='.$level, 'request_id='.$requestId, 'user='.$clean($_SERVER['REMOTE_USER'] ?? '-'), 'action='.$action];
    foreach ($fields as $key => $value) $parts[] = $key.'='.$clean($value);
    error_log('[UBB-KACHEL] '.implode(' ', $parts));
}
function respond(array $data = [], int $status = 200): never {
    global $requestId;
    if (($_SERVER['REQUEST_METHOD']??'')==='POST') event_log('INFO','request.end',['result'=>'ok','status'=>$status]);
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok'=>true,'requestId'=>$requestId,'data'=>$data], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}
function fail(string $code, string $message, int $status = 400): never {
    global $requestId;
    event_log('WARN','validation.error',['error_code'=>$code]);
    $action=$_GET['action']??'';
    if ($action==='backgrounds.upload') event_log('WARN','background.reject',['error_code'=>$code]);
    if ($action==='exports.save') event_log('WARN','export.failure',['error_code'=>$code]);
    if (($_SERVER['REQUEST_METHOD']??'')==='POST') event_log('WARN','request.end',['result'=>'error','status'=>$status]);
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok'=>false,'requestId'=>$requestId,'error'=>$code,'message'=>$message], JSON_UNESCAPED_UNICODE);
    exit;
}
function require_post(): void {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail('METHOD_NOT_ALLOWED','POST erforderlich.',405);
    if (!hash_equals(csrf(), $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) fail('CSRF','Sitzung abgelaufen. Bitte Seite neu laden.',403);
}
function body(): array {
    if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > MAX_TEMPLATE_BYTES) fail('TOO_LARGE','Anfrage zu groß.',413);
    $value = json_decode(file_get_contents('php://input'),true);
    if (!is_array($value)) fail('INVALID_JSON','Ungültiges JSON.');
    return $value;
}
function valid_id(mixed $id): string {
    if (!is_string($id) || !preg_match(ID_RX,$id)) fail('INVALID_ID','Ungültige ID.');
    return $id;
}
function safe_basename(string $name, string $fallback = 'datei'): string {
    $name = basename(str_replace('\\','/',$name));
    $name = pathinfo($name,PATHINFO_FILENAME);
    $name = iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$name) ?: $fallback;
    $name = trim(preg_replace('/[^A-Za-z0-9_-]+/','-',$name),'-_');
    return substr($name ?: $fallback,0,100);
}
function unique_path(string $dir, string $base, string $ext): string {
    for ($i=1;$i<10000;$i++) {
        $name = $base.($i===1?'':'-'.$i).'.'.$ext;
        $path=$dir.'/'.$name;
        if (is_file($path.'.json')) continue;
        $handle=@fopen($path,'x');
        if ($handle) { fclose($handle); return $path; }
    }
    fail('STORAGE_FULL','Kein freier Dateiname verfügbar.',500);
}
function atomic_json(string $path, array $data): void {
    $dir = dirname($path);
    if (!is_dir($dir) && !mkdir($dir,0775,true) && !is_dir($dir)) throw new RuntimeException('Ordner kann nicht angelegt werden');
    $lock = fopen($dir.'/.lock','c');
    if (!$lock || !flock($lock,LOCK_EX)) throw new RuntimeException('Sperre fehlgeschlagen');
    try {
        $tmp = tempnam($dir,'.tmp-');
        if (!$tmp) throw new RuntimeException('Temporäre Datei fehlgeschlagen');
        $json = json_encode($data,JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR);
        if (file_put_contents($tmp,$json) !== strlen($json) || !rename($tmp,$path)) { @unlink($tmp); throw new RuntimeException('Schreiben fehlgeschlagen'); }
    } finally { flock($lock,LOCK_UN); fclose($lock); }
}
function json_files(string $dir): array { return glob($dir.'/*.json') ?: []; }
function template_path(string $id): string { return storage('templates').'/'.valid_id($id).'.json'; }
function template_get(string $id): array {
    $path=template_path($id);
    if (!is_file($path)) fail('NOT_FOUND','Template nicht gefunden.',404);
    $t=json_decode(file_get_contents($path),true);
    if (!is_array($t)) fail('CORRUPT_TEMPLATE','Template-Datei beschädigt.',500);
    return $t;
}
function number(mixed $v, float $min, float $max): bool { return is_numeric($v) && is_finite((float)$v) && $v >= $min && $v <= $max; }
function validate_template(array $t): void {
    if (($t['schemaVersion']??null)!==1) fail('SCHEMA','Nur Template-Version 1 wird unterstützt.');
    valid_id($t['id']??null);
    if (!is_string($t['name']??null) || trim($t['name'])==='' || strlen($t['name'])>240) fail('INVALID_TEMPLATE','Name fehlt oder ist zu lang.');
    foreach (['width','height'] as $k) if (!number($t[$k]??null,100,6000)) fail('INVALID_TEMPLATE','Ungültige Canvasgröße.');
    if (!is_array($t['fields']??null) || !is_array($t['elements']??null) || count($t['fields'])>100 || count($t['elements'])>200) fail('INVALID_TEMPLATE','Ungültige Felder oder Elemente.');
    $ids=[];
    foreach ($t['fields'] as $f) {
        $id=valid_id($f['id']??null);
        if (isset($ids[$id]) || !in_array($f['inputType']??null,['text','textarea'],true) || !is_string($f['label']??null) || !is_string($f['defaultValue']??null)) fail('INVALID_FIELD','Ungültiges oder doppeltes Feld.');
        $ids[$id]=true;
    }
    $elementIds=[];
    foreach ($t['elements'] as $e) {
        $id=valid_id($e['id']??null);
        if (isset($elementIds[$id]) || !in_array($e['type']??null,['photo','text','shape','image'],true)) fail('INVALID_ELEMENT','Ungültiges oder doppeltes Element.');
        $elementIds[$id]=true;
        foreach (['x','y','width','height','rotation','opacity','zIndex'] as $k) if (!number($e[$k]??null,$k==='opacity'?0:($k==='width'||$k==='height'?1:-10000),$k==='opacity'?1:10000)) fail('INVALID_ELEMENT','Ungültige Elementgeometrie.');
        if ($e['type']==='text') {
            $b=$e['binding']??[];
            if (!in_array($b['type']??null,['field','static'],true) || ($b['type']==='field' && !isset($ids[$b['fieldId']??''])) || ($b['type']==='static' && !is_string($b['text']??null))) fail('INVALID_BINDING','Textbindung ungültig.');
            if (!number($e['minFontSize']??null,1,1000) || !number($e['maxFontSize']??null,(float)($e['minFontSize']??1),1000) || !number($e['maxLines']??null,1,100)) fail('INVALID_TEXT','Schriftgröße oder Zeilenanzahl ungültig.');
        }
        if ($e['type']==='image') {
            $asset=$e['asset']??'';
            if (!is_string($asset) || !preg_match('#^assets/template-assets/[A-Za-z0-9/_-]+\.(png|jpg|jpeg|webp|svg)$#D',$asset) || str_contains($asset,'..') || !is_file(ROOT.'/'.$asset)) fail('INVALID_ASSET','Bild-Asset ist nicht freigegeben oder fehlt.');
        }
    }
}
function image_upload(array $file, int $limit, array $allowed): array {
    if (($file['error']??UPLOAD_ERR_NO_FILE)!==UPLOAD_ERR_OK || !is_uploaded_file($file['tmp_name']??'')) fail('UPLOAD','Upload fehlgeschlagen.');
    if (($file['size']??0)<1 || $file['size']>$limit) fail('UPLOAD_SIZE','Datei überschreitet das Größenlimit.',413);
    $mime=(new finfo(FILEINFO_MIME_TYPE))->file($file['tmp_name']);
    $image=@getimagesize($file['tmp_name']);
    if (!$image || !isset($allowed[$mime]) || $image['mime']!==$mime) fail('UPLOAD_TYPE','Datei ist kein erlaubtes Bild.');
    if ($image[0]<1 || $image[1]<1 || $image[0]>12000 || $image[1]>12000) fail('UPLOAD_DIMENSIONS','Ungültige Bildgröße.');
    return [$allowed[$mime],$image[0],$image[1]];
}
