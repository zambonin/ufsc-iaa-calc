#!/usr/bin/env python
# -*- coding: utf-8 -*-

from getpass import getpass
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

    grades = []
    for i in range(2, len(hist), 7):
        grades.append((int(hist[i].text), float(hist[i+1].text)))

    weighted_grades, total_hours = 0, 0
    for h in grades:
        weighted_grades += h[0] * h[1]
        total_hours += h[0]

    return [weighted_grades, total_hours]

def get_current(browser):
    url = 'https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/'
    browser.open(url)

    if browser.url == url:
        mirror = browser.find_all(class_='rich-table-cell ')

        current = [i.text for i in mirror if "id2" in str(i)]
        disciplines = [(current[i], int(current[i+2])*18)
                            for i in range(3, len(current), 10)]

        name = browser.find(class_='aluno_info_col4').text
        return (name, disciplines)
    else:
        print("Falha de autenticação!")
        exit()

def possibilities(old_grades, current):
    from itertools import product

    grades, weights = old_grades[:], []
    for name, hours in current[1]:
        weights.append([poss/2 * hours for poss in range(21)])
        grades[1] += hours

    comb = set([sum(t) for t in product(*weights)])
    poss_iaa = sorted(set([round((grades[0] + i)/grades[1], 2) for i in comb]))

    return (poss_iaa[0], poss_iaa[-1])

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
