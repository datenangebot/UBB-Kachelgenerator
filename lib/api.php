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
        if (is_file($path.'.json') || is_file($path.'.preview.png')) continue;
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
function valid_template_asset(mixed $asset): bool {
    if (!is_string($asset) || strlen($asset)>512 ||
        !preg_match('~\Aassets/template-assets/.+\.(?:png|jpe?g|webp|svg)\z~iu', $asset) ||
        str_contains($asset, '..') || str_contains($asset, '\\') ||
        preg_match('/[\x00-\x1F\x7F]/', $asset)) return false;

    $assetDir=realpath(ROOT.'/assets/template-assets');
    $file=realpath(ROOT.'/'.$asset);
    return $assetDir!==false && $file!==false && is_file($file) &&
        str_starts_with($file, $assetDir.DIRECTORY_SEPARATOR);
}
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
            if (!valid_template_asset($asset)) fail('INVALID_ASSET','Bild-Asset fehlt oder liegt außerhalb von assets/template-assets/.');
        }
        if ($e['type']==='photo' && !empty($e['asset']) && !valid_template_asset($e['asset'])) fail('INVALID_ASSET','Standardfoto fehlt oder liegt außerhalb von assets/template-assets/.');
        if ($e['type']==='photo' && isset($e['crop'])) {
            if (!is_array($e['crop'])) fail('INVALID_CROP','Ungültiger Bildausschnitt.');
            foreach (['positionX','positionY','zoom'] as $k) if (!number($e['crop'][$k]??null,$k==='zoom'?1:0,$k==='zoom'?3:100)) fail('INVALID_CROP','Ungültiger Bildausschnitt.');
        }
    }
}

// All export types use the very same local font files in the browser and PDF.
function font_catalog(): array {
    $path=ROOT.'/assets/fonts/fonts.json';
    $fonts=is_file($path)?json_decode(file_get_contents($path),true):null;
    if (!is_array($fonts) || !$fonts) throw new RuntimeException('Schriftkatalog fehlt');
    foreach ($fonts as $font) {
        if (!is_string($font['family']??null) || !is_array($font['faces']??null) || !$font['faces']) throw new RuntimeException('Schriftkatalog ungültig');
        foreach ($font['faces'] as $face) {
            $file=$face['file']??'';
            $resolved=is_string($file)?realpath(ROOT.'/assets/fonts/'.$file):false;
            if (!$resolved || !str_starts_with($resolved,realpath(ROOT.'/assets/fonts').DIRECTORY_SEPARATOR) || !is_file($resolved) || !preg_match('/\.(ttf|otf)$/i',$file) || !number($face['weight']??null,100,900)) throw new RuntimeException('Schriftdatei fehlt oder ist ungültig');
        }
    }
    return $fonts;
}

function valid_background(mixed $filename): bool {
    if ($filename===null) return true;
    return is_string($filename) && $filename!=='' && basename($filename)===$filename &&
        !str_contains($filename,'\\') && !preg_match('/[\x00-\x1f\x7f]/',$filename) &&
        preg_match('/\.(png|jpe?g|webp)$/i',$filename) && is_file(storage('backgrounds').'/'.$filename);
}

function restorable_state(mixed $s): bool {
    if (!is_array($s) || ($s['version']??null)!==EXPORT_STATE_VERSION || !is_array($s['template']??null)) return false;
    $t=$s['template'];
    if (($t['schemaVersion']??null)!==1 || !is_string($t['id']??null) || !preg_match(ID_RX,$t['id']) || !is_string($t['name']??null) || !number($t['width']??null,100,6000) || !number($t['height']??null,100,6000) || !is_array($t['fields']??null) || !is_array($t['elements']??null)) return false;
    if (!is_array($s['fields']??null) || !is_array($s['photo']??null) || !is_array($s['textOverrides']??null) || !array_key_exists('background',$s) || !valid_background($s['background'])) return false;
    foreach ($t['fields'] as $f) {
        if (!is_array($f) || !is_string($f['id']??null) || !is_string($s['fields'][$f['id']]??null) || strlen($s['fields'][$f['id']])>100000) return false;
    }
    foreach (['positionX','positionY','zoom'] as $key) if (!number($s['photo'][$key]??null,$key==='zoom'?1:0,$key==='zoom'?3:100)) return false;
    $textIds=[];
    foreach ($t['elements'] as $e) {
        if (!is_array($e) || !is_string($e['id']??null) || !in_array($e['type']??null,['photo','image','text','shape'],true)) return false;
        if ($e['type']==='text') $textIds[$e['id']]=true;
        if ($e['type']==='image' && !valid_template_asset($e['asset']??null)) return false;
        if ($e['type']==='photo' && !empty($e['asset']) && !valid_template_asset($e['asset'])) return false;
    }
    foreach ($s['textOverrides'] as $id=>$o) {
        if (!isset($textIds[$id]) || !is_array($o) || !in_array($o['mode']??null,['auto','manual'],true) || !number($o['size']??null,0,1000) || !number($o['x']??null,-100,100) || !number($o['y']??null,-100,100)) return false;
    }
    return true;
}

function export_get(string $id): array {
    foreach (glob(storage('exports').'/*/*/*.json')?:[] as $path) {
        $item=json_decode(file_get_contents($path),true);
        if (is_array($item) && ($item['id']??null)===$id) return $item;
    }
    fail('NOT_FOUND','Export nicht gefunden.',404);
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
