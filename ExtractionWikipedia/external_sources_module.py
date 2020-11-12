"""
Module regroupant les fonctions utilisée pour parser les informations des sources externes
"""
###################  WIKIPEDIA ###################
# Fonctions utilisées dans le notebook wikipédia #
##################################################


from Identification_couples_livres.extract_books_from_DB import *

def format_list(page):
    """
    Prend une page wikipédia et supprime les indications de colonnes pour permettre au parseur de trouver les listes
    :param str page: page wikipédia
    :return: même page sans {{colonnes|taille=|nombre=2| ... }} tout en conservant le contenu
    """
    page = re.sub(r'\*\*', '*', page)
    page_serach_re = re.search(r'\{\{colonnes\|.*?\|\n', page, re.DOTALL)
    while page_serach_re:
        nb_bracket = 0
        start_index = page_serach_re.span()[0]
        for index, caractere in enumerate(page[start_index:]):
            if caractere == '{':
                nb_bracket += 1
            elif caractere == '}':
                nb_bracket -= 1
            if nb_bracket == 0:
                page = page[:start_index + index - 1] + page[start_index + index + 2:]
                page = re.sub(r'\{\{colonnes\|.*?\|\n', '', page)
                break
        page_serach_re = re.search(r'\{\{colonnes\|.*?\|\n', page, re.DOTALL)
    return page

def split_info_box(page):
    """
    Sépare un page wikipédia en son infobox et le reste de la page. Si il n'y a pas d'Infobox, retourne un champs vide
    pour L'infobox, et la page complete pour le reste de la page
    :param str page: page wikipédia
    :return (str, str): Infobox et contenu de la page sans l'infobox
    """
    nb_bracket = 0
    start_index = page.find("{{Infobox")
    for index, caractere in enumerate(page[start_index:]):
        if caractere == '{':
            nb_bracket += 1
        elif caractere == '}':
            nb_bracket -= 1
        if nb_bracket == 0:
            return page[:start_index + index + 1], page[start_index + index + 2:]
    return "", page

def get_info_from_infobox(raw_infos):
    """
    retourne les champs de l'infobox sous forme de dictionnaire à partir de sa chaine de caractère, ou si
    :param str raw_infos: chaine de caractère de l'infobox
    :return dict[str, str]: champs de l'infobox
    """
    infos = {}
    for info in re.split(r"\n\||\n\}", raw_infos, flags=re.DOTALL)[1:-1]:
        if len(info.split('=')) > 1:
            key, value = info.split('=')[0], info.split('=')[1]
            infos[key] = value
    return infos


def parse_section(section, title_ls, level):
    """
    Trie les informations que l'on peut récupérer à part d'une section tirée du parseur,
    et fait de même pour ses sous-sections si elles existent
    :param wikitextparser.Section section: Section de la page wikipedia
    :param set title_ls: liste des intitulés des sections
    :param int level: Niveau de la section (section principale, secondaire, tertiaire, etc...)
    :return dict[str: UNION[dict, list, int]]: informations pertinantes sur la section et ses sous-sections
    """

    section_dict = {'content': section.contents,
                    'list': [re.sub(r"\'\'", "", item) for list in section.get_lists() for item in list.items],
                    'sub_section': {},
                    'level':level
                    }

    # les deux premières sections sont toujours: "\n", section_actuelle
    if len(section.sections) > 2:
        sub_sections = section.sections[2:]
        for sub_sect in sub_sections:
            # On verifie bien qu'ils sagit de sous-sections
            if sub_sect.level == level + 1:
                title_ls.add(sub_sect.title)
                # Si il y a des sous-sections, on applique la fonction sur celles-ci
                section_dict['sub_section'][sub_sect.title] = parse_section(sub_sect, title_ls, sub_sect.level)

    return section_dict

def extract_title_from_list(list):
    """
    Extrait le titre des livres depuis les listes d'items générée par le parseur
    2 étapes:
        - Si les données sont structurées : {{Ouvrage|titre=... }}, on récupère directement le titre
        - Si les donnée ne sont pas structurée: ''L'Effet des rayons gamma sur les vieux garçons'' (de [[Paul Zindel]]), Leméac ([[1970]])
          On doit eliminer les infornations en trop et ne garder que le titre.
    :param list[str] list: liste du parseur d'où extraire les titres
    :return list[str]: liste comportant uniquement les informations des titres
    """
    titles = []
    for item in [item.replace('\n', '') for item in list]:
        added = False

        # Si les informations sur les livres sont structurées
        meta_data_re = re.search(r"\{\{(Ouvrage|Écrit).*\}\}", item)
        if meta_data_re:
            meta_data = meta_data_re.group()
            # On selectionne le titre et le sous titre
            title_re = re.search(r'(?<=titre=).*?(?=\|)', meta_data)
            subtitle_re = re.search(r'(?<=sous-titre=).*?(?=\|)', meta_data)
            # Quand un sous-titre est présent, C'est souvent un tome d'une série. On concatène le titre et le sous-titre
            if title_re or subtitle_re:
                added = True
                if title_re and subtitle_re:
                    titles.append(normalize(title_re.group() + ' ' + subtitle_re.group()))
                elif title_re:
                    titles.append(normalize(title_re.group()))
                elif subtitle_re:
                    titles.append(normalize(subtitle_re.group()))

        # Si les informations ne sont pas structurées, ou que l'extraction a échouée
        if not added:
            # On retire les "{{ ...  }}", ce sont des méta-data
            n = 1
            while n:
                item, n = re.subn(r"\{\{.*\}\}", '', item)
            n = 1
            # On retire les balises html, ce sont des liens vers d'autres pages
            while n:
                item, n = re.subn(r"<.+?>.*?</.+?>", '', item)
            # On seletionne les élements entre [[...]]
            brackets_re = re.search(r'(?<=\[\[).*?(?=\]\])', item)
            while brackets_re:
                # Si on rencontre cette configuration: [[info1|info2|info3]], il s'agit de la même information
                # sous plusieures formes différentes. On choisi arbitrairement la dernière et on supprime les [[ et ]]
                item = re.sub(r"\[\[.*?\]\]", brackets_re.group().split('|')[-1], item, count=1)
                brackets_re = re.search(r'(?<=\[\[).*?(?=\]\])', item)
            # On retire dans l'ordre le texte entre parenthèse, les reférences, les années en début de chaine,
            # les espaces, les tirets et les ":" en début de chaine.
            item = remove_text_between_parentheses(item)
            item = re.sub(r'<ref .+?\\>', '', item)
            item = re.sub(r'^\s*?\d{4}', '', item)
            item = re.sub(r'^-\s', '', item)
            item = re.sub(r'^:', '', item)
            if normalize(item.split(',')[0]):
                titles.append(normalize(item.split(',')[0]))

    return titles