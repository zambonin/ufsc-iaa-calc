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

    hours = [int(hist[i].text) for i in range(2, len(hist), 7)]
    grades = [float(hist[i].text) for i in range(3, len(hist), 7)]

    weigh_grades = sum([h*g for h, g in zip(hours, grades)])
    total_hours = sum(hours)

    return [weigh_grades, total_hours]

def get_actual(browser):
    url = 'https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/'
    browser.open(url)

    if browser.url == url:
        mirror = browser.find_all(class_='rich-table-cell ')

        actual = [i.text for i in mirror if "id2" in str(i)]
        disciplines = [(actual[i], int(actual[i+2])*18)
                            for i in range(3, len(actual), 10)]

        nome = browser.find(class_='aluno_info_col4').text
        return (nome, disciplines)
    else:
        print("Falha de autenticação!")
        exit()

username = input("Insira sua matrícula: ")
password = getpass("Insira sua senha do CAGR: ")

browser = login(username, password)
history = get_history(browser)
actual = get_actual(browser)

iaa = history[0] / history[1]
print("Olá, %s! Seu IAA é %.2f." % (actual[0], iaa))

for name, hours in actual[1]:
    grade = float(input("Possível nota em %s: " % name))
    while grade > 10 or grade < 0:
        grade = float(input("Nota inválida. Possível nota: "))
    history[0] += grade * hours
    history[1] += hours

new_iaa = history[0] / history[1]
print ("Com as notas informadas, seu possível IAA será %.2f." % new_iaa)
