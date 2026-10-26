import msgs, namefix, re
BS=chr(92)
T=msgs.load('rom14.nds')
def lines(s):
    for c in 'nfr': s=s.replace(BS+c,'\x00')
    return s.split('\x00')
def w(l): return len(re.sub(r'\{[0-9A-F]{4}\}','x',l.replace('{01DE}',' ').replace('{01AE}','…')))
allw=sorted(w(l) for b in T if len(b)<200 for s in b for l in lines(s) if '{FFFE}' not in l)
print('99.5%', allw[int(len(allw)*0.995)], '99.9%', allw[int(len(allw)*0.999)], 'max', allw[-1])
for b,i in sorted(set(namefix.plan())|set(namefix.CRY)):
    s=T[b][i]; t=namefix.fix(b,i,s)
    for lo,ln in zip(lines(s),lines(t)):
        if w(ln)>w(lo) and w(ln)>15: print('%d:%d %d→%d | %s'%(b,i,w(lo),w(ln),ln))
