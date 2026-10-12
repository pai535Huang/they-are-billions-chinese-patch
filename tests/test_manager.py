import hashlib,json,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class InstallerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);base=Path(self.tmp.name);self.release=base/'release';self.release.mkdir();self.game=base/'steamapps/common/They Are Billions';self.workshop=base/'steamapps/workshop/content/644930/1559552741';self.game.mkdir(parents=True);self.workshop.mkdir(parents=True);self.targets=[];files=[]
  shutil.copy2(ROOT/'templates/manage_patch.py',self.release/'manage_patch.py')
  for i,(name,area) in enumerate([('ZXStrings.dat','game'),('ZXCampaignStrings.dat','game'),('Strings.csv','official_workshop_1559552741')]):
   old=('original-'+str(i)).encode();new=('patched-'+str(i)).encode();on='original-'+str(i);pn='patch-'+str(i);(self.release/on).write_bytes(old);(self.release/pn).write_bytes(new);target=(self.game if area=='game' else self.workshop)/name;target.write_bytes(old);self.targets.append(target)
   oh=hashlib.sha256(old).hexdigest();nh=hashlib.sha256(new).hexdigest();files.append(dict(relative=name,area=area,original=on,previous=on,patched=pn,original_sha256=oh,previous_sha256=oh,patched_sha256=nh,allowed_hashes=[oh,nh]))
  self.manifest={'files':files};(self.release/'manifest.json').write_text(json.dumps(self.manifest))
 def run_action(self,action):return subprocess.run([sys.executable,str(self.release/'manage_patch.py'),action,'--game-dir',str(self.game)],capture_output=True,text=True)
 def test_install_and_restore(self):
  for action,key in [('install','patched_sha256'),('restore','original_sha256')]:
   r=self.run_action(action);self.assertEqual(r.returncode,0,r.stderr)
   for f,p in zip(self.manifest['files'],self.targets):self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f[key])
 def test_unknown_target_stops_all_writes(self):
  self.targets[1].write_bytes(b'unknown');before=[p.read_bytes() for p in self.targets];r=self.run_action('install');self.assertNotEqual(r.returncode,0);self.assertEqual([p.read_bytes() for p in self.targets],before)
 def test_corrupt_payload_stops_all_writes(self):
  (self.release/self.manifest['files'][2]['patched']).write_bytes(b'corrupt');before=[p.read_bytes() for p in self.targets];r=self.run_action('install');self.assertNotEqual(r.returncode,0);self.assertEqual([p.read_bytes() for p in self.targets],before)
class DataTests(unittest.TestCase):
 def test_translation_schema(self):
  for filename in ['text.json','names.json','glossary.json']:
   data=json.loads((ROOT/'translations'/filename).read_text());self.assertTrue(data)
   mappings=data.values() if filename=='text.json' else [data]
   for mapping in mappings:
    self.assertIsInstance(mapping,dict)
    for key,value in mapping.items():self.assertIsInstance(key,str);self.assertIsInstance(value,str)
 def test_public_version_config(self):
  config=json.loads((ROOT/'config.json').read_text());self.assertEqual(config['workshop_id'],'1559552741');self.assertEqual(len(config['source_hashes']),3)
  for value in config['source_hashes'].values():self.assertRegex(value,r'^[0-9a-f]{64}$')
if __name__=='__main__':unittest.main()
