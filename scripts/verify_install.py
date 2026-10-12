from pathlib import Path
import tempfile,json,shutil,subprocess,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];release=ROOT/'releases/v0.3';m=json.loads((release/'manifest.json').read_text())
with tempfile.TemporaryDirectory(prefix='tab-patch-test-') as td:
 root=Path(td)/'steamapps';game=root/'common/They Are Billions';ws=root/'workshop/content/644930/1559552741';game.mkdir(parents=True);ws.mkdir(parents=True)
 targets=[]
 for f in m['files']:
  p=(game if f['area']=='game' else ws)/f['relative'];shutil.copy2(release/f['previous'],p);targets.append(p)
 for action in ['install','restore','install','previous','install']:
  r=subprocess.run([sys.executable,str(release/'manage_patch.py'),action,'--game-dir',str(game)],capture_output=True,text=True)
  assert r.returncode==0,r.stderr+r.stdout
  key={'install':'patched','restore':'original','previous':'previous'}[action]
  for f,p in zip(m['files'],targets):assert hashlib.sha256(p.read_bytes()).hexdigest()==f[key+'_sha256']
 targets[1].write_bytes(b'unknown-version');before=[p.read_bytes() for p in targets]
 r=subprocess.run([sys.executable,str(release/'manage_patch.py'),'restore','--game-dir',str(game)],capture_output=True,text=True)
 assert r.returncode!=0 and [p.read_bytes() for p in targets]==before
print('通过：三文件安装/原版恢复/previous原版回退及未知版本拦截；仅使用临时副本。')
