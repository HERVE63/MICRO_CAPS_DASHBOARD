"""Tests purs du reveil mensuel MICRO CAPS : aucune donnees ni journal modifies."""
from datetime import datetime
from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location("planning",Path(__file__).resolve().parents[1]/"SCRIPTS_ACTIFS/00A_PLANIFICATION_QUOTIDIENNE.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test():
 cas=[
  ("2026-09-29T21:58:00+00:00","45 21 * * 2","45 22 * * 2"),
  ("2026-10-27T23:11:00+00:00","45 22 * * 2","45 21 * * 2"),
  ("2026-11-24T23:11:00+00:00","45 22 * * 2","45 21 * * 2"),
 ]
 for instant,bon,mauvais in cas:
  d=datetime.fromisoformat(instant)
  assert m.decider("schedule",bon,d,mode="MENSUEL")["run"] is True
  assert m.decider("schedule",mauvais,d,mode="MENSUEL")["run"] is False
 assert m.decider("workflow_dispatch",maintenant=datetime.fromisoformat("2026-10-23T18:00:00+00:00"),mode="MENSUEL")["run"]
 print("REVEIL_MENSUEL_OK: retard, ete/hiver, bascule DST, reprise explicite")
if __name__=="__main__":test()
