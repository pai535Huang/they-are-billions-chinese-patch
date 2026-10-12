from pathlib import Path
import argparse,json,hashlib,os,tempfile
folder=Path(__file__).resolve().parent;m=json.loads((folder/'manifest.json').read_text())
p=argparse.ArgumentParser(description='官方中文资源补丁：请先退出游戏')
p.add_argument('action',choices=['install','restore','previous'])
p.add_argument('--game-dir',type=Path,default=Path.home()/'.local/share/Steam/steamapps/common/They Are Billions')
a=p.parse_args();key={'install':'patched','restore':'original','previous':'previous'}[a.action]
def sha(b):return hashlib.sha256(b).hexdigest()
def write_atomic(target,data,mode):
 fd,tmp=tempfile.mkstemp(prefix='.TAB-Chinese-',dir=target.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(tmp,mode);os.replace(tmp,target)
 finally:Path(tmp).unlink(missing_ok=True)
prepared=[]
for item in m['files']:
 base=a.game_dir if item['area']=='game' else a.game_dir.parent.parent/'workshop/content/644930/1559552741'
 target=base/item['relative'];old=target.read_bytes();data=(folder/item[key]).read_bytes()
 if sha(old) not in item['allowed_hashes']:raise SystemExit('当前文件不匹配已验证版本，停止覆盖：'+str(target))
 if sha(data)!=item[key+'_sha256']:raise SystemExit('补丁或备份校验失败：'+item[key])
 prepared.append((target,old,data,target.stat().st_mode & 0o777))
completed=[]
try:
 for target,old,data,mode in prepared:
  if old==data:continue
  write_atomic(target,data,mode);completed.append((target,old,mode))
  assert target.read_bytes()==data
except BaseException:
 for target,old,mode in reversed(completed):write_atomic(target,old,mode)
 raise
print({'install':'v0.3主文本、官方战役和官方50日挑战补丁已安装。','restore':'三个官方资源均已恢复原版。','previous':'已恢复此构建所使用的原版资源。'}[a.action])
