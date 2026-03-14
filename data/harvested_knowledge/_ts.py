import urllib.request, json, time
for model in ['llama3.2:latest', 'mistral:latest']:
    t = time.time()
    try:
        payload = json.dumps({'model':model,'prompt':'List 3 benefits of AI tools.','stream':False,'options':{'num_predict':60,'temperature':0.5}}).encode()
        req = urllib.request.Request('http://localhost:11434/api/generate',data=payload,headers={'Content-Type':'application/json'})
        r = json.loads(urllib.request.urlopen(req,timeout=90).read())
        print(model, round(time.time()-t,1), 's:', r.get('response','')[:80])
    except Exception as e:
        print(model, round(time.time()-t,1), 's FAIL:', str(e)[:60])
