<?php
declare(strict_types=1);
require_once __DIR__.'/../lib/api.php';
set_exception_handler(function(Throwable $e): never { event_log('ERROR','exception',['error_code'=>get_class($e)]); fail('SERVER_ERROR','Interner Fehler. Details im Serverprotokoll.',500); });
$action=$_GET['action']??'';
if ($_SERVER['REQUEST_METHOD']==='POST') { require_post(); event_log('INFO','request.start',['operation'=>$action]); }
switch ($action) {
case 'backgrounds.list':
    $items=[];
    foreach (glob(storage('backgrounds').'/*')?:[] as $path) {
        if (!is_file($path) || !preg_match('/\.(jpe?g|png|webp)$/i',$path)) continue;
        $size=@getimagesize($path); if (!$size) continue;
        $items[]=['filename'=>basename($path),'url'=>'storage/backgrounds/'.rawurlencode(basename($path)),'width'=>$size[0],'height'=>$size[1],'size'=>filesize($path),'modifiedAt'=>date(DATE_ATOM,filemtime($path))];
    }
    usort($items,fn($a,$b)=>strcmp($b['modifiedAt'],$a['modifiedAt'])); respond($items);
case 'backgrounds.upload':
    [$ext,$w,$h]=image_upload($_FILES['image']??[],MAX_IMAGE_BYTES,['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp']);
    $dir=storage('backgrounds'); if (!is_dir($dir)) mkdir($dir,0775,true);
    $path=unique_path($dir,safe_basename($_FILES['image']['name']),$ext);
    if (!move_uploaded_file($_FILES['image']['tmp_name'],$path)) { @unlink($path); throw new RuntimeException('Upload verschieben fehlgeschlagen'); }
    event_log('INFO','background.upload',['filename'=>basename($path),'size'=>filesize($path)]);
    respond(['filename'=>basename($path),'url'=>'storage/backgrounds/'.rawurlencode(basename($path)),'width'=>$w,'height'=>$h]);
case 'templates.list':
    $items=[]; foreach (json_files(storage('templates')) as $path) { $t=json_decode(file_get_contents($path),true); if (is_array($t)) $items[]=['id'=>$t['id'],'name'=>$t['name'],'width'=>$t['width'],'height'=>$t['height'],'updatedAt'=>$t['updatedAt']??null]; }
    usort($items,fn($a,$b)=>strcmp($a['name'],$b['name'])); respond($items);
case 'templates.get': respond(template_get(valid_id($_GET['id']??null)));
case 'templates.save':
    $t=body(); $createOnly=($t['createOnly']??false)===true; unset($t['createOnly']); validate_template($t);
    $path=template_path($t['id']); $exists=is_file($path);
    if ($createOnly && $exists) fail('CONFLICT','Template-ID existiert bereits.',409);
    $t['updatedAt']=date(DATE_ATOM); if (!$exists) $t['createdAt']=$t['updatedAt'];
    atomic_json($path,$t); event_log('INFO',$exists?'template.update':'template.create',['template'=>$t['id']]); respond($t);
case 'templates.duplicate':
    $b=body(); $source=template_get(valid_id($b['sourceId']??null));
    $source['id']=valid_id($b['id']??null); $source['name']=trim((string)($b['name']??''));
    validate_template($source); if (is_file(template_path($source['id']))) fail('CONFLICT','Template-ID existiert bereits.',409);
    $source['createdAt']=$source['updatedAt']=date(DATE_ATOM); atomic_json(template_path($source['id']),$source);
    event_log('INFO','template.duplicate',['template'=>$source['id']]); respond($source);
case 'templates.delete':
    $b=body(); $id=valid_id($b['id']??null); $path=template_path($id);
    if (!is_file($path)) fail('NOT_FOUND','Template nicht gefunden.',404);
    if (!unlink($path)) throw new RuntimeException('Löschen fehlgeschlagen');
    event_log('INFO','template.delete',['template'=>$id]); respond(['id'=>$id]);
case 'exports.save':
    event_log('INFO','export.start');
    $meta=json_decode($_POST['metadata']??'',true); if (!is_array($meta)) fail('INVALID_METADATA','Exportdaten fehlen.');
    $format=$meta['format']??'';
    if (!in_array($format,['png','jpg'],true)) fail('INVALID_FORMAT','Exportformat ungültig.');
    [$ext,$w,$h]=image_upload($_FILES['image']??[],MAX_EXPORT_BYTES,$format==='png'?['image/png'=>'png']:['image/jpeg'=>'jpg']);
    $template=template_get(valid_id($meta['templateId']??null));
    $scale=$meta['scale']??null;
    if (!in_array($scale,[1,2],true) || $w!=(int)$template['width']*$scale || $h!=(int)$template['height']*$scale) fail('INVALID_DIMENSIONS','Exportabmessungen passen nicht zum Template.');
    $dir=storage('exports').'/'.date('Y/m'); if (!is_dir($dir) && !mkdir($dir,0775,true)) throw new RuntimeException('Exportordner fehlt');
    $path=unique_path($dir,safe_basename((string)($meta['filename']??'UBB-Kachel'),'UBB-Kachel'),$ext);
    if (!move_uploaded_file($_FILES['image']['tmp_name'],$path)) { @unlink($path); throw new RuntimeException('Exportdatei kann nicht gespeichert werden'); }
    $id=bin2hex(random_bytes(6)); $relative='storage/exports/'.date('Y/m').'/'.basename($path);
    $sidecar=['id'=>$id,'createdAt'=>date(DATE_ATOM),'filename'=>basename($path),'url'=>$relative,'format'=>$format,'width'=>$w,'height'=>$h,'scale'=>$scale,'templateId'=>$template['id'],'templateName'=>$template['name'],'generatorState'=>is_array($meta['generatorState']??null)?$meta['generatorState']:[]];
    try { atomic_json($path.'.json',$sidecar); } catch(Throwable $e) { @unlink($path); throw $e; }
    event_log('INFO','export.success',['filename'=>basename($path),'format'=>$format,'width'=>$w,'height'=>$h]); respond($sidecar);
case 'exports.list':
    $items=[]; foreach (glob(storage('exports').'/*/*/*.json')?:[] as $path) { $x=json_decode(file_get_contents($path),true); if (is_array($x) && isset($x['url'])) $items[]=$x; }
    usort($items,fn($a,$b)=>strcmp($b['createdAt'],$a['createdAt'])); respond($items);
default: fail('NOT_FOUND','Endpunkt nicht gefunden.',404);
}
