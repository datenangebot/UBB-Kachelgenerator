<?php
declare(strict_types=1);
require_once __DIR__.'/../lib/api.php';
set_exception_handler(function(Throwable $e): never { event_log('ERROR','exception',['error_code'=>get_class($e)]); fail('SERVER_ERROR','Interner Fehler. Details im Serverprotokoll.',500); });
$action=$_GET['action']??'';
if ($_SERVER['REQUEST_METHOD']==='POST') { require_post(); event_log('INFO','request.start',['operation'=>$action]); }
switch ($action) {
case 'fonts.list': respond(font_catalog());
case 'assets.list':
    $items=[]; $dir=ROOT.'/assets/template-assets';
    if (is_dir($dir)) foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir,FilesystemIterator::SKIP_DOTS)) as $file) {
        if (!$file->isFile()) continue;
        $path=$file->getPathname(); $asset='assets/template-assets/'.substr($path,strlen($dir)+1);
        if (!valid_template_asset($asset)) continue;
        $size=@getimagesize($path);
        if (!$size && strtolower(pathinfo($path,PATHINFO_EXTENSION))!=='svg') continue;
        $meta=is_file($path.'.json')?json_decode(file_get_contents($path.'.json'),true):null;
        $addedAt=is_string($meta['addedAt']??null)&&strtotime($meta['addedAt'])!==false?$meta['addedAt']:date(DATE_ATOM,filemtime($path));
        $items[]=['asset'=>$asset,'url'=>implode('/',array_map('rawurlencode',explode('/',$asset))),'filename'=>basename($path),'name'=>is_string($meta['name']??null)?$meta['name']:basename($path),'addedAt'=>$addedAt,'width'=>$size?$size[0]:null,'height'=>$size?$size[1]:null];
    }
    usort($items,fn($a,$b)=>strcmp($b['addedAt'],$a['addedAt'])?:strcmp($a['asset'],$b['asset'])); respond($items);
case 'assets.upload':
    [$ext,$w,$h]=image_upload($_FILES['image']??[],MAX_IMAGE_BYTES,['image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp']);
    $dir=ROOT.'/assets/template-assets';
    if (!is_dir($dir) && !mkdir($dir,0775,true)) throw new RuntimeException('Assetordner fehlt');
    $path=unique_path($dir,safe_basename($_FILES['image']['name']).'-'.bin2hex(random_bytes(4)),$ext);
    $name=basename(str_replace('\\','/',$_FILES['image']['name']));
    if (!preg_match('//u',$name) || strlen($name)>512) $name=basename($path);
    $name=preg_replace('/[\x00-\x1F\x7F]/u',' ',$name);
    try {
        if (!move_uploaded_file($_FILES['image']['tmp_name'],$path)) throw new RuntimeException('Asset kann nicht gespeichert werden');
        atomic_json($path.'.json',['name'=>$name,'addedAt'=>(new DateTimeImmutable())->format('Y-m-d\TH:i:s.vP')]);
    } catch(Throwable $e) { @unlink($path); throw $e; }
    event_log('INFO','asset.upload',['filename'=>basename($path)]);
    respond(['asset'=>'assets/template-assets/'.basename($path),'width'=>$w,'height'=>$h]);
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
    if (strlen($_POST['metadata']??'')>MAX_TEMPLATE_BYTES*2) fail('TOO_LARGE','Exportmetadaten zu groß.',413);
    $meta=json_decode($_POST['metadata']??'',true); if (!is_array($meta)) fail('INVALID_METADATA','Exportdaten fehlen.');
    $format=$meta['format']??'';
    if (!in_array($format,['png','jpg','pdf'],true)) fail('INVALID_FORMAT','Exportformat ungültig.');
    [$ext,$w,$h]=image_upload($_FILES['image']??[],MAX_EXPORT_BYTES,$format==='jpg'?['image/jpeg'=>'jpg']:['image/png'=>'png']);
    $templateId=valid_id($meta['templateId']??null);
    $generatorState=is_array($meta['generatorState']??null)?$meta['generatorState']:[];
    if (array_key_exists('version',$generatorState)) {
        if (!restorable_state($generatorState)) fail('INVALID_STATE','Generatorzustand ist unvollständig oder ungültig.');
        $template=$generatorState['template']; validate_template($template);
        if ($template['id']!==$templateId || strlen(json_encode($template,JSON_THROW_ON_ERROR))>MAX_TEMPLATE_BYTES) fail('INVALID_STATE','Template-Kopie passt nicht zum Export.');
    } else $template=template_get($templateId);
    $scale=$meta['scale']??null;
    if (!in_array($scale,[1,2],true) || $w!=(int)$template['width']*$scale || $h!=(int)$template['height']*$scale) fail('INVALID_DIMENSIONS','Exportabmessungen passen nicht zum Template.');
    if ($format==='pdf') {
        $file=$_FILES['document']??[];
        if (($file['error']??UPLOAD_ERR_NO_FILE)!==UPLOAD_ERR_OK || !is_uploaded_file($file['tmp_name']??'')) fail('UPLOAD','PDF-Upload fehlgeschlagen.');
        if (($file['size']??0)<1 || $file['size']>MAX_EXPORT_BYTES) fail('UPLOAD_SIZE','PDF überschreitet das Größenlimit.',413);
        $pdf=file_get_contents($file['tmp_name']);
        if ((new finfo(FILEINFO_MIME_TYPE))->file($file['tmp_name'])!=='application/pdf' || !preg_match('/\A%PDF-1\.[4-7]/',$pdf) || !preg_match('/%%EOF\s*\z/',$pdf) || preg_match_all('~/Type\s*/Page\b~',$pdf)!==1 || !preg_match('~/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]~',$pdf,$box) || abs((float)$box[1]-$w*.75)>.01 || abs((float)$box[2]-$h*.75)>.01) fail('INVALID_PDF','PDF ist ungültig oder hat eine falsche Seitengröße.');
        $ext='pdf';
    }
    $dir=storage('exports').'/'.date('Y/m'); if (!is_dir($dir) && !mkdir($dir,0775,true)) throw new RuntimeException('Exportordner fehlt');
    $path=unique_path($dir,safe_basename((string)($meta['filename']??'UBB-Kachel'),'UBB-Kachel'),$ext);
    $previewPath=$format==='pdf'?$path.'.preview.png':null;
    $id=bin2hex(random_bytes(6)); $relative='storage/exports/'.date('Y/m').'/'.basename($path);
    $sidecar=['id'=>$id,'createdAt'=>date(DATE_ATOM),'filename'=>basename($path),'url'=>$relative,'previewUrl'=>$format==='pdf'?$relative.'.preview.png':$relative,'format'=>$format,'width'=>$w,'height'=>$h,'scale'=>$scale,'templateId'=>$template['id'],'templateName'=>$template['name'],'generatorState'=>$generatorState];
    try {
        if (!move_uploaded_file($_FILES[$format==='pdf'?'document':'image']['tmp_name'],$path)) throw new RuntimeException('Exportdatei kann nicht gespeichert werden');
        if ($previewPath && !move_uploaded_file($_FILES['image']['tmp_name'],$previewPath)) throw new RuntimeException('Exportvorschau kann nicht gespeichert werden');
        atomic_json($path.'.json',$sidecar);
    } catch(Throwable $e) { @unlink($path); if ($previewPath) @unlink($previewPath); throw $e; }
    event_log('INFO','export.success',['filename'=>basename($path),'format'=>$format,'width'=>$w,'height'=>$h]); respond($sidecar);
case 'exports.get':
    $item=export_get(valid_id($_GET['id']??null));
    if (!restorable_state($item['generatorState']??null)) fail('NOT_RESTORABLE','Dieser Export enthält keinen vollständig wiederherstellbaren Generatorzustand.',409);
    validate_template($item['generatorState']['template']);
    respond($item);
case 'exports.list':
    $items=[]; foreach (glob(storage('exports').'/*/*/*.json')?:[] as $path) {
        $x=json_decode(file_get_contents($path),true);
        if (is_array($x) && isset($x['url'])) {
            $x['canRestore']=restorable_state($x['generatorState']??null);
            unset($x['generatorState']); $items[]=$x;
        }
    }
    usort($items,fn($a,$b)=>strcmp($b['createdAt'],$a['createdAt'])); respond($items);
default: fail('NOT_FOUND','Endpunkt nicht gefunden.',404);
}
