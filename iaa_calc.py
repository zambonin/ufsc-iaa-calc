#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import reduce
from getpass import getpass
from itertools import product
from robobrowser import RoboBrowser


def login(user, passwd):
    browser = RoboBrowser(history=True, parser='html.parser')
    browser.open('https://sistemas.ufsc.br/login')

    form = browser.get_form(id='fm1')
    form['username'].value = user
    form['password'].value = passwd
    browser.submit_form(form)

    return browser


def get_history(browser):
    browser.open("https://cagr.sistemas.ufsc.br/"
                 "modules/aluno/historicoEscolar/")
    hist = browser.find_all(class_='rich-table-cell ')

    grades = [[int(hours.text), float(grade.text)]
              for hours, grade in zip(hist[2::7], hist[3::7])]

    return grades


def get_current(browser):
    url = 'https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/'
    browser.open(url)

    if browser.url == url:
        mirror = browser.find_all(class_='rich-table-cell ')

        current = [i.text for i in mirror if "id2" in str(i)]
        disciplines = [(name, int(hours)*18) for name, hours in
                       zip(current[3::10], current[5::10])]

        student = browser.find(class_='aluno_info_col4').text
        return (student, disciplines)
    else:
        print("Falha de autenticação!")
        raise SystemExit


def round_iaa(grade):
    if isinstance(grade, list):
        return float(str(grade[0] / grade[1])[:4])
    return float(str(grade)[:4])


def round_ufsc(grade):
    decimal = grade % 1
    if decimal < .25:
        return float(int(grade))
    if (.25 <= decimal < .75):
        return float(int(grade) + 0.5)
    if decimal >= .75:
        return float(int(grade) + 1)


def ia_calc(grades):
    weight, total_hours = reduce(
        lambda g, w: [g[0]+(w[0]*w[1]), g[1]+w[0]], grades, [0, 0])
    return [weight, total_hours]


def iaa_poss(old_grades, current):
    grades, weights = ia_calc(old_grades), []
    for name, hours in current[1]:
        weights.append([poss/2 * hours for poss in range(21)])
        grades[1] += hours

    comb = set(map(sum, product(*weights)))
    poss_iaa = set([(grades[0] + i)/grades[1] for i in comb])

    return (round_iaa(min(poss_iaa)), round_iaa(max(poss_iaa)))


username = input("Insira sua matrícula: ")
password = getpass("Insira sua senha do CAGR: ")

browser = login(username, password)
history, current = get_history(browser), get_current(browser)

print("Olá, {}! Seu IAA é {}.".format(current[0], round_iaa(ia_calc(history))))

var = input("Deseja saber quanto seu IAA pode variar neste semestre? [s/N]: ")
if var.lower() == 's':
    print('Seu IAA pode variar de {} a {}.'
          .format(*iaa_poss(history, current)))

for name, hours in current[1]:
    while True:
        try:
            grade = float(input("Possível nota em {}: ".format(name)))
            if not (0 <= grade <= 10):
                raise ValueError
            break
        except ValueError:
            print("Nota inválida.")
    history.append([hours, round_ufsc(grade)])

iaa = round_iaa(ia_calc(history))
ia = round_iaa(ia_calc(history[-len(current[1]):]))
iap = round_iaa(ia_calc([i for i in history if i[1] >= 6]))

print("Com as notas informadas, suas métricas serão:")
print("IAA: \033[1m{}\033[0m \t IA: {} \t IAP: {}".format(iaa, ia, iap))
