from pathlib import Path
import os,json,zipfile,shutil,runpy,hashlib
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
if not shutil.which('7z'):raise SystemExit('需要PATH中的7z命令。')
release=ROOT/'releases/v0.3';previous=json.loads((release/'manifest.json').read_text()) if (release/'manifest.json').exists() else {}
build=ROOT/'build';stage=build/'release';build.mkdir(exist_ok=True)
if stage.exists():shutil.rmtree(stage)
stage.mkdir()
config=json.loads((ROOT/'config.json').read_text())
keys=config['archive_keys']
for relative,expected in config['source_hashes'].items():
 p=ROOT/'originals'/('official-50-days/Strings.csv' if relative=='50Days.Strings.csv' else relative)
 if not p.exists():raise SystemExit('缺少原版资源，请先运行 python3 scripts/prepare.py')
 if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise SystemExit('原版资源不匹配：'+relative)
for name in ['ZXStrings.dat','ZXCampaignStrings.dat']:
 with zipfile.ZipFile(ROOT/'originals'/name) as z:
  assert z.namelist()==[name]
  (build/(name.removesuffix('.dat')+'.raw')).write_bytes(z.read(name,pwd=keys[name].encode()))
(build/'campaign_password.txt').write_text(keys['ZXCampaignStrings.dat'])
runpy.run_path(str(ROOT/'scripts/build_main.py'),run_name='__main__')
runpy.run_path(str(ROOT/'scripts/build_official.py'),run_name='__main__')
m=json.loads((stage/'manifest.json').read_text())
oldfiles={(f['area'],f['relative']):f for f in previous.get('files',[])}
for f in m['files']:
 old=oldfiles.get((f['area'],f['relative']),{})
 f['allowed_hashes']=sorted(set(f['allowed_hashes']+old.get('allowed_hashes',[])+([old['patched_sha256']] if old.get('patched_sha256') else [])))
(stage/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
for p in (ROOT/'templates').iterdir():shutil.copy2(p,stage/p.name)
for p in (ROOT/'docs').iterdir():
 if p.is_file() and p.suffix=='.md':shutil.copy2(p,stage/p.name)
shutil.copytree(ROOT/'docs/screenshots',stage/'排版截图')
p=stage/'排版验证.md';p.write_text(p.read_text().replace('screenshots/','排版截图/'))
p=stage/'修订对照.md';p.write_text(p.read_text().replace('未修改ZXCampaignStrings.dat、创意工坊地图及模组文本。','独立官方战役包及官方50日挑战也已修订，详见官方资源修订.json。玩家自制内容文件未修改。'))
(stage/'构建记录.json').write_text(json.dumps({'game_installation_touched':False,'source_files':'local originals/','validation':'XML and ZIP roundtrip; visual report is the recorded v0.3 check, not a new runtime test'},ensure_ascii=False,indent=2))
release.parent.mkdir(exist_ok=True)
if release.exists():shutil.rmtree(release)
shutil.copytree(stage,release)
shutil.make_archive(str(ROOT/'releases/they-are-billions-chinese-v0.3'),'zip',root_dir=ROOT/'releases',base_dir='v0.3')
print('构建完成：'+str(release))
