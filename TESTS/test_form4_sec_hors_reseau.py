"""Test XML Form 4 hors reseau, sans confusion achats/attributions."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("form4",ROOT/"SCRIPTS_ACTIFS/07Y_EXTRAIRE_FORM4_SEC.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test():
 xml=b"""<?xml version="1.0"?>
<ownershipDocument><reportingOwner><reportingOwnerId><rptOwnerName>Jane Example</rptOwnerName></reportingOwnerId></reportingOwner>
<nonDerivativeTable><nonDerivativeTransaction><transactionDate><value>2026-09-15</value></transactionDate>
<transactionCoding><transactionCode>P</transactionCode></transactionCoding>
<transactionAmounts><transactionShares><value>100</value></transactionShares>
<transactionPricePerShare><value>5.50</value></transactionPricePerShare>
<transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode></transactionAmounts>
<postTransactionAmounts><sharesOwnedFollowingTransaction><value>1500</value></sharesOwnedFollowingTransaction></postTransactionAmounts>
<ownershipNature><directOrIndirectOwnership><value>D</value></directOrIndirectOwnership></ownershipNature>
</nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>"""
 rows=mod.analyser_xml(xml)
 assert len(rows)==1
 assert rows[0]["Code_transaction"]=="P"
 assert rows[0]["Titres_transaction"]=="100"
 assert rows[0]["Dirigeants_declares"]=="Jane Example"
 assert rows[0]["Statut_interpretation"]=="A_VERIFIER_NATURE_FINANCEMENT_ET_PROPRIETE"
 print("TEST FORM 4 OK: XML, code, titres, dirigeant, statut non valide")
if __name__=="__main__":test()
