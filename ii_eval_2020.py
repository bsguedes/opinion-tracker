import unicodedata


def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


names = [
 ['adilson mohr', ['mor']],
 ['aless oliveira', ['alessander']],
 ['alethea soares', ['aletea', 'aleteia', 'aletheia']],
 ['alexandre azevedo', ['alex']],
 ['andrei engeroff', ['andrey']],
 ['arthur foscarini', ['artur']],
 ['bernardo berra'],
 ['bruno guedes'],
 ['camila alves'],
 ['caren nichele', ['karen']],
 ['diego rosso'],
 ['edisson braga', ['ed', 'eddie']],
 ['fernando friedrich', ['fernando f']],
 ['fernando mello', ['melo']],
 ['gabrielle marchioro', ['gabi', 'gabriele', 'gaby']],
 ['gilton guma'],
 ['guilherme schmitt', ['gui']],
 ['jean carli'],
 ['juliane schroeder', ['ju']],
 ['julio pires'],
 ['kin gusmao', ['kim']],
 ['lucas araujo', ['lucas a']],
 ['lucas longaray', ['longest', 'long', 'lucas l']],
 ['lucas zampieri', ['zampiere', 'zam', 'zan', 'lucas z']],
 ['lucia spier'],
 ['marcio riveiro'],
 ['paola dias'],
 ['patricia pizzinato', ['pati', 'paty']],
 ['thiago lottici', ['tiago']],
]


forbidden = ['fernando', 'lucas']


def evaluate_string(raw_input):
    form_input = strip_accents(raw_input.strip().lower())
    if form_input in forbidden:
        return None
    for name in names:
        split_name = name[0].split(' ')
        if form_input == name[0] or form_input == split_name[0] or form_input == split_name[1]:
            return name[0]
    for name in names:
        if len(name) > 1:
            for var in name[1]:
                if var in form_input:
                    return name[0]
    return None
