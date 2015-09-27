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
    browser.open('https://cagr.sistemas.ufsc.br/modules/aluno/historicoEscolar/')
    hist = browser.find_all(class_='rich-table-cell ')

    grades = [[int(hours.text), float(grade.text)]
                for hours, grade in zip(hist[2::7], hist[3::7])]

    weight, total_hours = reduce(
        lambda g, w: [g[0]+(w[0]*w[1]), g[1]+w[0]], grades, [0, 0])

    return [weight, total_hours]

def get_current(browser):
    url = 'https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/'
    browser.open(url)

    if browser.url == url:
        mirror = browser.find_all(class_='rich-table-cell ')

        current = [i.text for i in mirror if "id2" in str(i)]
        disciplines = [(name, int(hours)*18) for name,
                            hours in zip(current[3::10], current[5::10])]

        student = browser.find(class_='aluno_info_col4').text
        return (student, disciplines)
    else:
        print("Falha de autenticação!")
        exit()

def possibilities(old_grades, current):
    grades, weights = old_grades[:], []
    for name, hours in current[1]:
        weights.append([poss/2 * hours for poss in range(21)])
        grades[1] += hours

    comb = set(map(sum, product(*weights)))
    poss_iaa = set([round((grades[0] + i)/grades[1], 2) for i in comb])

    return (min(poss_iaa), max(poss_iaa))

username = input("Insira sua matrícula: ")
password = getpass("Insira sua senha do CAGR: ")

browser = login(username, password)
history, current = get_history(browser), get_current(browser)

print("Olá, %s! Seu IAA é %.2f." % (current[0], history[0] / history[1]))

var = input("Deseja saber o quanto seu IAA pode variar neste semestre? [s/N]: ")
if var == 's' or var == 'S':
    print('Seu IAA pode variar de %.2f a %.2f.'
            % possibilities(history, current))

for name, hours in current[1]:
    grade = float(input("Possível nota em %s: " % name))
    while grade > 10 or grade < 0:
        grade = float(input("Nota inválida. Possível nota: "))
    history[0] += grade * hours
    history[1] += hours

new_iaa = history[0] / history[1]
print ("Com as notas informadas, seu possível IAA será %.2f." % new_iaa)
