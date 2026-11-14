"""Cours bruts, unité explicite, preuve conservée et cache jamais promu en clôture."""
import gzip,hashlib,json,math,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
BASE=Path(__file__).resolve().parents[1]
ARCHIVES=BASE/'AUDITS/HISTORIQUES_PUBLICS_40'
CACHE=BASE/'AUDITS/COURS_QUOTIDIENS'

def normaliser_cours(value,currency):
    value=float(value)
    if not math.isfinite(value) or value<=0:raise ValueError('Cours non positif ou non fini')
    if currency in ('GBp','GBX'):return value/100,'GBP'
    if currency not in {'EUR','USD','GBP','CAD','SEK','DKK','NOK','CHF'}:raise ValueError('Unité non vérifiée : '+str(currency))
    return value,currency

def serie(raw):
    tz=ZoneInfo(raw['meta'].get('exchangeTimezoneName','UTC'))
    pairs=[]
    for ts,v in zip(raw.get('timestamp',[]),raw['indicators']['quote'][0]['close']):
        if v is not None and math.isfinite(float(v)) and float(v)>0:
            pairs.append((datetime.fromtimestamp(ts,tz).date().isoformat(),float(v)))
    return pd.Series(dict(pairs),dtype=float).sort_index()

def charger(ticker,date_limite):
    limit=str(date_limite)[:10];safe=urllib.parse.quote(ticker,safe='.=^-')
    paths=list(ARCHIVES.glob('*/'+safe+'.json.gz'))+list(CACHE.glob('*/'+safe+'.json.gz'))
    for p in sorted(paths,key=lambda p:p.parent.name,reverse=True):
        raw=json.loads(gzip.decompress(p.read_bytes()));meta=raw.get('meta',{})
        if meta.get('symbol','').upper()!=ticker.upper():continue
        captured=datetime.strptime(p.parent.name,'%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        day=captured.astimezone(ZoneInfo(meta.get('exchangeTimezoneName','UTC'))).date().isoformat()
        closing=meta.get('currentTradingPeriod',{}).get('regular',{}).get('end')
        settled=limit<day or (limit==day and closing and captured.timestamp()>=closing+1800)
        prices=serie(raw)
        if settled and not prices.empty and prices.index.max()>=limit:return raw,str(p.relative_to(BASE))
    errors=[]
    for host in ('query1.finance.yahoo.com','query2.finance.yahoo.com'):
        url='https://'+host+'/v8/finance/chart/'+urllib.parse.quote(ticker,safe='')+'?range=3mo&interval=1d&events=div%2Csplits'
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'MicroCapsResearch/1.0'})
            with urllib.request.urlopen(req,timeout=20) as resp:result=json.load(resp)
            raw=result['chart']['result'][0]
            if raw['meta'].get('symbol','').upper()!=ticker.upper():raise ValueError('Identité divergente')
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');folder=CACHE/stamp;folder.mkdir(parents=True,exist_ok=True)
            data=json.dumps(raw,ensure_ascii=False,allow_nan=False).encode();p=folder/(safe+'.json.gz')
            p.write_bytes(gzip.compress(data,mtime=0))
            (folder/(safe+'.preuve.json')).write_text(json.dumps({'url':url,'collecte_utc':stamp,'sha256_payload':hashlib.sha256(data).hexdigest()},indent=2))
            return raw,str(p.relative_to(BASE))
        except Exception as exc:errors.append(type(exc).__name__+':'+str(getattr(exc,'code','')))
    raise RuntimeError('Cours indisponibles '+ticker+' '+','.join(errors))

def cloture(ticker,date_limite):
    raw,proof=charger(ticker,date_limite);prices=serie(raw);prices=prices[prices.index<=str(date_limite)[:10]]
    if prices.empty:raise RuntimeError('Aucune clôture antérieure à '+str(date_limite))
    price,currency=normaliser_cours(prices.iloc[-1],raw['meta'].get('currency'))
    return {'cours':price,'date':prices.index[-1],'devise':currency,'unite_source':raw['meta']['currency'],'preuve':proof}

def suspension(ticker,date_reference):
    p=BASE/'CONFIG/CONTROLES_MARCHE_DOCUMENTES.json'
    for r in json.loads(p.read_text()) if p.exists() else []:
        if r['ticker']==ticker and r['debut']<=str(date_reference)[:10] and not r.get('date_reprise'):return r
    return None
