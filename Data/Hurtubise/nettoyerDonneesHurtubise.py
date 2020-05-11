

f = open('Exportation-Hurtubise.txt')
lignes = f.readlines()
lignesValides = [l for l in lignes if l.startswith('Éditions Hurtubise')]
f.close()

f = open('Exportation-Hurtubise-Nettoye.txt','w')
for l in lignesValides:
    f.write(l)
f.close()
    
        
