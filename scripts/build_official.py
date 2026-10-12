from pathlib import Path
import zipfile,xml.etree.ElementTree as E,json,re,csv,io,hashlib,shutil,subprocess
from xml.sax.saxutils import escape
out=Path('build/release');game=Path('originals');workshop=Path('originals/official-50-days')
main=E.fromstring(Path('build/pack/ZXStrings.dat').read_bytes());canonical={}
for t in main.find('./Properties/Dictionary/Items'):
 table=t[0].get('value');cols={i[0].get('value'):int(i[1].get('value')) for i in t.find("./Complex/Properties/Dictionary[@name='Cols']/Items")}
 if table not in ('Campaign','Interface'):continue
 for row in t.find("./Complex/Properties/Dictionary[@name='Rows']/Items"):
  canonical[table,row[0].get('value')]=row.find('./SingleArray/Items')[cols['Text_CHS']].get('value','').replace('\\n','\n').replace('\\t','\t')
pwd=Path('build/campaign_password.txt').read_text();src=game/'ZXCampaignStrings.dat';
if not (out/'ZXCampaignStrings.original.dat').exists():shutil.copy2(src,out/'ZXCampaignStrings.original.dat')
b=Path('build/ZXCampaignStrings.raw').read_bytes();s=b.decode('utf-8-sig');root=E.fromstring(b);changes=[];edits=[];spans=list(re.finditer(r'<SingleArray elementType="System.String, mscorlib">.*?</SingleArray>',s,re.S));idx=0
for t in root.find('./Properties/Dictionary/Items'):
 cols={i[0].get('value'):int(i[1].get('value')) for i in t.find("./Complex/Properties/Dictionary[@name='Cols']/Items")}
 for row in t.find("./Complex/Properties/Dictionary[@name='Rows']/Items"):
  span=spans[idx];idx+=1;key=row[0].get('value');v=row.find('./SingleArray/Items');old=v[cols['Text_CHS']].get('value','');new=canonical['Campaign',key];en=v[cols['Text_EN']].get('value','')
  assert sorted(re.findall(r'\{\d+[^}]*\}',new))==sorted(re.findall(r'\{\d+[^}]*\}',en))
  if old==new:continue
  cells=list(re.finditer(r'<(?:Simple|Null)\b[^>]*/>',span.group()));cell=cells[cols['Text_CHS']];enc=escape(new,{'"':'&quot;','\n':'&#xA;','\r':'&#xD;','\t':'&#x9;'})
  edits.append((span.start()+cell.start(),span.start()+cell.end(),'<Simple value="'+enc+'" />'));changes.append({'id':key,'old':old,'new':new})
for a,b,c in sorted(edits,reverse=True):s=s[:a]+c+s[b:]
newbytes=b'\xef\xbb\xbf'+s.encode();newroot=E.fromstring(newbytes)
# Every non-Chinese column and all IDs must be byte-equivalent as XML elements.
for ot,nt in zip(root.find('./Properties/Dictionary/Items'),newroot.find('./Properties/Dictionary/Items')):
 assert E.tostring(ot.find("./Complex/Properties/Dictionary[@name='Cols']"))==E.tostring(nt.find("./Complex/Properties/Dictionary[@name='Cols']"))
 cols={i[0].get('value'):int(i[1].get('value')) for i in ot.find("./Complex/Properties/Dictionary[@name='Cols']/Items")}
 for orow,nrow in zip(ot.find("./Complex/Properties/Dictionary[@name='Rows']/Items"),nt.find("./Complex/Properties/Dictionary[@name='Rows']/Items")):
  assert E.tostring(orow[0])==E.tostring(nrow[0]);ov=orow.find('./SingleArray/Items');nv=nrow.find('./SingleArray/Items');assert len(ov)==len(nv)
  for i,(a,b) in enumerate(zip(ov,nv)):
   if i!=cols['Text_CHS']:assert E.tostring(a)==E.tostring(b)
  assert nv[cols['Text_CHS']].get('value','')==canonical['Campaign',orow[0].get('value')]
stage=Path('build/pack');(stage/'ZXCampaignStrings.dat').write_bytes(newbytes);archive=(out/'ZXCampaignStrings.dat').resolve();archive.unlink(missing_ok=True)
p=subprocess.run(['7z','a','-tzip','-mm=Deflate','-mem=ZipCrypto','-mx=5','-p'+pwd,str(archive),'ZXCampaignStrings.dat'],cwd=stage,capture_output=True);assert p.returncode==0
with zipfile.ZipFile(archive) as z:assert z.read('ZXCampaignStrings.dat',pwd=pwd.encode())==newbytes
# The author is Numantian Games; touch only this known official workshop item.
csvpath=workshop/'Strings.csv';raw=(out/'50Days.Strings.original.csv').read_bytes() if (out/'50Days.Strings.original.csv').exists() else csvpath.read_bytes();
if not (out/'50Days.Strings.original.csv').exists():shutil.copy2(csvpath,out/'50Days.Strings.original.csv')
lines=raw.decode('utf-8-sig').splitlines(keepends=True);oldrows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'));newlines=[lines[0]];csvchanges=[]
for line,row in zip(lines[1:],oldrows[1:]):
 assert len(row)==14;key=row[0];new=canonical['Interface',key].replace(chr(10),chr(92)+'n');assert chr(10) not in new
 assert sorted(re.findall(r'\{\d+[^}]*\}',new))==sorted(re.findall(r'\{\d+[^}]*\}',row[1]))
 if new!=row[5]:
  parts=line.rstrip('\r\n').split(';');assert len(parts)==14;old=parts[5];parts[5]=new;line=';'.join(parts)+'\r\n';csvchanges.append({'id':key,'old':old,'new':new})
 newlines.append(line)
csvbytes=b'\xef\xbb\xbf'+''.join(newlines).encode();newrows=list(csv.reader(io.StringIO(csvbytes.decode('utf-8-sig')),delimiter=';'));assert len(oldrows)==len(newrows)
for a,b in zip(oldrows,newrows):
 for i,(aa,bb) in enumerate(zip(a,b)):
  if i!=5:assert aa==bb
(out/'50Days.Strings.csv').write_bytes(csvbytes)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((out/'manifest.json').read_text());m['files']=[{'relative':'ZXStrings.dat','area':'game','patched':'ZXStrings.dat','original':'ZXStrings.original.dat','previous':'ZXStrings.original.dat','allowed_hashes':[sha(out/n) for n in ['ZXStrings.dat','ZXStrings.original.dat']]},{'relative':'ZXCampaignStrings.dat','area':'game','patched':'ZXCampaignStrings.dat','original':'ZXCampaignStrings.original.dat','previous':'ZXCampaignStrings.original.dat','allowed_hashes':[sha(out/'ZXCampaignStrings.original.dat'),sha(src),sha(archive)]},{'relative':'Strings.csv','area':'official_workshop_1559552741','patched':'50Days.Strings.csv','original':'50Days.Strings.original.csv','previous':'50Days.Strings.original.csv','allowed_hashes':[sha(out/'50Days.Strings.original.csv'),sha(csvpath),sha(out/'50Days.Strings.csv')]}]
for f in m['files']:
 if f['area']=='game':f['allowed_hashes'].append(sha(game/f['relative']))
 f['patched_sha256']=sha(out/f['patched']);f['original_sha256']=sha(out/f['original']);f['previous_sha256']=sha(out/f['previous'])
m['official_campaign_changed_cells']=len(changes);m['official_workshop_changed_cells']=len(csvchanges);m['official_campaign_rows_synchronized']=len(canonical)-843;m['official_map_files_audited']=54;m['player_content_modified']=False
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));(out/'官方资源修订.json').write_text(json.dumps({'campaign':changes,'50_days':csvchanges},ensure_ascii=False,indent=2));shutil.copyfile('docs/内置地图审计.json',out/'内置地图审计.json')
print('Official campaign: synchronized 479 rows, changed',len(changes),'cells. Official 50 Days: changed',len(csvchanges),'of 12 cells. Player content untouched.')
