from pathlib import Path
import xml.etree.ElementTree as E
from xml.sax.saxutils import escape
import json,re,zipfile,subprocess,hashlib,shutil,collections
out=Path('build/release');out.mkdir(parents=True,exist_ok=True)
base=Path('originals')
original=base/'ZXStrings.dat'
assert hashlib.sha256(original.read_bytes()).hexdigest()==json.loads(Path('config.json').read_text())['source_hashes']['ZXStrings.dat']
shutil.copy2(original,out/'ZXStrings.original.dat')
b=Path('build/ZXStrings.raw').read_bytes();s=b.decode('utf-8-sig')
changes=json.loads(Path('translations/text.json').read_text());names=json.loads(Path('translations/names.json').read_text());glossary=json.loads(Path('translations/glossary.json').read_text())
root=E.fromstring(b);spans=list(re.finditer(r'<SingleArray elementType="System.String, mscorlib">.*?</SingleArray>',s,re.S));pos=0;edits=[];audit=[];seen=set();reviewed=collections.Counter();expected={}
def ph(t):return sorted(re.findall(r'\{\d+(?:[^}]*)\}',t))
for item in root.find('./Properties/Dictionary/Items'):
 table=item[0].get('value');prop=item.find('./Complex/Properties')
 cols={i[0].get('value'):int(i[1].get('value')) for i in prop.find("./Dictionary[@name='Cols']/Items")}
 for row in prop.find("./Dictionary[@name='Rows']/Items"):
  block=spans[pos];pos+=1;key=row[0].get('value');vals=row.find('./SingleArray/Items');cells=list(re.finditer(r'<(?:Simple|Null)\b[^>]*/>',block.group()))
  assert len(cells)==len(vals)
  for field,index in cols.items():
   if not field.endswith('_CHS'):continue
   old=vals[index].get('value','');new=old;kind='术语统一'
   enfield=field[:-4]+'_EN';en=vals[cols[enfield]].get('value','') if enfield in cols else ''
   if (field=='Description_CHS' if table=='Entities' else field=='Text_CHS') and key in changes.get(table,{}):
    seen.add((table,key));new=changes[table][key];kind='对照英文修订';reviewed[table]+=1
    assert ph(new)==ph(en),(table,key,'English placeholders',ph(new),ph(en))
   if table=='Entities' and field=='Name_CHS' and key in names:
    new=names[key];kind='名称修订'
   for a,c in glossary.items():new=new.replace(a,c)
   if new==old:continue
   assert ph(new)==ph(en) if kind!='术语统一' else ph(new)==ph(old),(table,key,field,'placeholders')
   encoded=escape(new,{'"':'&quot;','\n':'&#xA;','\r':'&#xD;','\t':'&#x9;'})
   cell=cells[index];edits.append((block.start()+cell.start(),block.start()+cell.end(),'<Simple value="'+encoded+'" />'))
   expected[table,key,index]=new;audit.append(dict(table=table,id=key,field=field,en=en,old=old,new=new,kind=kind))
assert seen=={(t,k) for t,rows in changes.items() for k in rows},'Unknown revision ID'
assert pos==len(spans)
for start,end,new in sorted(edits,reverse=True):s=s[:start]+new+s[end:]
patched=b'\xef\xbb\xbf'+s.encode('utf-8');r2=E.fromstring(patched)
oldtables=root.find('./Properties/Dictionary/Items');newtables=r2.find('./Properties/Dictionary/Items');assert len(oldtables)==len(newtables)
for a,c in zip(oldtables,newtables):
 table=a[0].get('value');assert E.tostring(a[0])==E.tostring(c[0]);assert E.tostring(a.find('./Complex/Properties/Dictionary[@name="Cols"]'))==E.tostring(c.find('./Complex/Properties/Dictionary[@name="Cols"]'))
 ar=a.find('./Complex/Properties/Dictionary[@name="Rows"]/Items');cr=c.find('./Complex/Properties/Dictionary[@name="Rows"]/Items');assert len(ar)==len(cr)
 for row1,row2 in zip(ar,cr):
  key=row1[0].get('value');assert E.tostring(row1[0])==E.tostring(row2[0]);v1=row1.find('./SingleArray/Items');v2=row2.find('./SingleArray/Items');assert len(v1)==len(v2)
  for i,(o,n) in enumerate(zip(v1,v2)):
   if (table,key,i) in expected:assert n.tag=='Simple' and n.get('value')==expected[table,key,i]
   else:assert E.tostring(o)==E.tostring(n),(table,key,i,'unexpected change')
stage=Path('build/pack');stage.mkdir(exist_ok=True);(stage/'ZXStrings.dat').write_bytes(patched)
pwd='1847022185176208962489145797518470221851762089624891457975334454FADSFASDF45345'
archive=(out/'ZXStrings.dat').resolve();archive.unlink(missing_ok=True)
p=subprocess.run(['7z','a','-tzip','-mm=Deflate','-mem=ZipCrypto','-mx=5','-p'+pwd,str(archive),'ZXStrings.dat'],cwd=stage,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
with zipfile.ZipFile(archive) as z:
 assert z.namelist()==['ZXStrings.dat'];assert z.read('ZXStrings.dat',pwd=pwd.encode())==patched
manifest={ 'version':'0.3','game_version':'1.0.14','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'modified_cells':len(audit),'modified_rows':len({(x['table'],x['id']) for x in audit}),'by_table':dict(collections.Counter(x['table'] for x in audit)),'by_kind':dict(collections.Counter(x['kind'] for x in audit)),'checked_selected_rows':dict(reviewed)}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(out/'revisions.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
shutil.copyfile('translations/text.json',out/'translation_overrides.json');shutil.copyfile('translations/names.json',out/'name_overrides.json');shutil.copyfile('translations/glossary.json',out/'glossary.json')
md='# 中文修订 v0.3\n\n以已验证的Steam 1.0.14原版为基准，累计修改'+str(len(audit))+'个简体中文单元格（含术语统一）。继承v0.1的修订。\n\n'
md+='覆盖科技名称、战役教程和任务说明、要塞标牌、剧情字幕、旧时代新闻档案、建筑与单位说明、帮助、游戏提示、属性、更新说明及部分界面。不是全量重译；未修改ZXCampaignStrings.dat、创意工坊地图及模组文本。\n\n## 修订对照\n\n'
for x in audit:md+='### '+x['table']+' / '+x['id']+' / '+x['field']+'\n\n原版：'+x['old']+'\n\n修订：'+x['new']+'\n\n'
(out/'修订对照.md').write_text(md)
(out/'结构校验报告.json').write_text(json.dumps({'xml_parses':True,'all_non_chs_cells_unchanged':True,'row_ids_and_column_definitions_unchanged':True,'format_placeholders_valid':True,'archive_roundtrip_matches':True,'archive_member':'ZXStrings.dat','game_rules_untouched':True},indent=2))
print(json.dumps(manifest,ensure_ascii=False,indent=2))
