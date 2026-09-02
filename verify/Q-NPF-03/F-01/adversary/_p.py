import json
d=json.load(open('adversary/a2_worlds.json',encoding='utf-8'))
print("baseline:", d["checks"][0]["row"])
print("chart mean level:", d["chart_mean_level"])
for r in d["checks"][1]["rows"]:
    print(r)
