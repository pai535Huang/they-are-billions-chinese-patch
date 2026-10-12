"""Copy supported original localization assets into the ignored local originals/ directory."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description='准备本地原版资源；不修改游戏安装。')
p.add_argument('--game-dir',type=Path,default=Path.home()/'.local/share/Steam/steamapps/common/They Are Billions')
p.add_argument('--backup-dir',type=Path,help='可选：使用此前补丁包内的original备份文件')
a=p.parse_args();config=json.loads((ROOT/'config.json').read_text());stock=ROOT/'originals'
items=[('ZXStrings.dat','ZXStrings.dat','ZXStrings.original.dat'),('ZXCampaignStrings.dat','ZXCampaignStrings.dat','ZXCampaignStrings.original.dat'),('50Days.Strings.csv','official-50-days/Strings.csv','50Days.Strings.original.csv')]
prepared=[]
for name,relative,backup in items:
 target=stock/relative
 if a.backup_dir:source=a.backup_dir/backup
 elif target.exists():source=target
 elif name=='50Days.Strings.csv':source=a.game_dir.parent.parent/'workshop/content/644930'/config['workshop_id']/'Strings.csv'
 else:source=a.game_dir/name
 if not source.exists():raise SystemExit('缺少资源：'+str(source)+'。请安装游戏及官方50日挑战，或指定--backup-dir。')
 data=source.read_bytes()
 if hashlib.sha256(data).hexdigest()!=config['source_hashes'][name]:raise SystemExit('资源版本不匹配或已打过补丁：'+str(source)+'。请使用匹配版本的原版备份；不会修改游戏。')
 prepared.append((target,data))
for target,data in prepared:
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():target.write_bytes(data)
 elif target.read_bytes()!=data:raise SystemExit('现有备份不同，停止覆盖：'+str(target))
print('原版资源已准备；Steam安装未修改。')
