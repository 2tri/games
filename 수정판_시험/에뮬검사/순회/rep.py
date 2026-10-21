import json,sys
f=sys.argv[1]
for l in open(f):
    d=json.loads(l); r=d['res'] or {}
    k=d.get('feat') or [(d.get('kind'),d.get('var'),d.get('val'))]
    print(d['i'],'맵',d['map'],d.get('obj',''),d.get('xy',(d.get('x'),d.get('y'))),[tuple(x) for x in k][:2],'| 쪽',r.get('pages'),'전투',r.get('battles'),'후보',r.get('cand'),'이동',r.get('map_after_warp'),'끝대화' if r.get('end_dialog') else '','끝메뉴' if r.get('end_menu') else '')
