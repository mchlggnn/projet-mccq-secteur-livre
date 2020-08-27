import json
import Levenshtein

from tqdm import tqdm
from extraction_croissement import *

with open('couple_wiki.json', 'r') as couples_file:
    couples = json.load(couples_file)

confirmed_couple = []
unconfirmed_couple = []
for couple in tqdm(couples, total=len(couples)):
    if isinstance(couple['book wiki'], dict):
        keys = list(couple['book wiki'].keys())
        for key in keys:
            couple['book wiki'][normalize(key)] = normalize(couple['book wiki'][key])
        if 'auteur' in couple['book wiki'] and couple['book wiki']['auteur']:
            correspondance = False
            for author in couple['book DB']['author']:
                test = (couple['book wiki']['auteur'], author)
                dist_auteur = Levenshtein.distance(couple['book wiki']['auteur'], author)
                if dist_auteur < max(1, min(len(couple['book wiki']['auteur']), len(author)) / 4):
                    confirmed_couple.append(couple)
                    correspondance = True
                    break
            if not correspondance:
                unconfirmed_couple.append(couple)
    else:
        print('a faire a la main: titre DB=', couple['titre DB'],' titre wiki=', couple['titre wiki'], ' wiki text=', couple['book wiki'][:200])
print('nombre de correspondance: ', len(confirmed_couple))
print('nombre de distinct: ', len(unconfirmed_couple))
print('confirmed_couple:')
# print(json.dumps(confirmed_couple, indent=2))
print('unconfirmed_couple:')
# print(json.dumps(unconfirmed_couple, indent=2))

test_auteurs = ['Michel Tremblay', 'Anne Hébert', 'Gabrielle Roy', 'Marie Cardinal', 'Réjean Ducharme',
                'Jacques Ferron', 'Victor-Lévy Beaulieu', 'Marcel Dubé', 'Yves Thériault', 'Jacques Poulin',
                'André Langevin']