"""Non-Windows font fallback preserves multilingual financial report content."""
import pathlib
import sys
import io
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import exports
import pdfplumber


def run():
    timestamp='2026-10-08T02:00:00+00:00'
    report={'id':'portable-test','revision':1,'status':'draft','created_at':timestamp,'updated_at':timestamp,
        'actual_income':'10.00','actual_expenses':'2.00','variance_reason':'收据核对完成',
        'rows':[{'kind':'expense','budget_ref':'unplanned','description':'活动用品 — 测试',
                 'amount':'2.00','evidence_ids':[]}], 'history':[]}
    original=pathlib.Path.exists
    def exists(path):
        return False if str(path).replace('\\','/')=='C:/Windows/Fonts/simsun.ttc' else original(path)
    with patch.object(pathlib.Path,'exists',exists):
        raw=exports.finance_pdf(report,{'title':'校园文化交流','revenue':[],'expenses':[]},{'name':'中华文化协会'})
    output=ROOT/'.agency'/'qa'/'portable-finance.pdf';output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(raw)
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        text=''.join(page.extract_text() or '' for page in pdf.pages)
    assert '中华文化协会' in text and '校园文化交流' in text and '活动用品' in text,text
    print('PASS: no-Windows-font financial PDF retains Chinese club/event/transaction text.')


if __name__=='__main__':run()
