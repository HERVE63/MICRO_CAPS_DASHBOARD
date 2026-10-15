"""Le CIK iXBRL présent, absent ou multiple ne reçoit pas le même statut."""
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('controle_us',Path(__file__).resolve().parents[1]/'SCRIPTS_ACTIFS/07AG_CONTROLER_DOCUMENTS_US.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 assert m.cik_document(b'<html><ix:nonNumeric name="dei:EntityCentralIndexKey">1328792</ix:nonNumeric></html>')=={'0001328792'}
 assert m.cik_document(b'<html><body>No CIK</body></html>')==set()
 assert m.cik_document(b'<html><ix:nonNumeric name="dei:EntityCentralIndexKey">1328792</ix:nonNumeric><ix:nonNumeric name="dei:EntityCentralIndexKey">2</ix:nonNumeric></html>')=={'0001328792','0000000002'}
 assert m.cik_document(b'<html><ix:nonNumeric name="dei:EntityCentralIndexKey"><span>0001328792</span></ix:nonNumeric></html>')=={'0001328792'}
 print('CONTROLE DOCUMENTS US: CIK unique, multiple, absent et balisé distingués')
if __name__=='__main__':test()
