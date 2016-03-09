#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import reduce
from getpass import getpass
from operator import mul
from robobrowser import RoboBrowser


def login(user, passwd):
    browser = RoboBrowser(history=True, parser="html.parser")
    browser.open("https://sistemas.ufsc.br/login")

    form = browser.get_form(id="fm1")
    form["username"].value = user
    form["password"].value = passwd
    browser.submit_form(form)

    return browser


def get_student(browser):
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/cadastro/"
    browser.open(url)

    if browser.url == url:
        return browser.find(class_="rich-panel-header ").text
    raise SystemExit("Falha de autenticação!")


def get_history(browser):
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/historicoEscolar/"
    browser.open(url)

    hist = browser.find_all(class_="rich-table-cell ")
    grades = [[int(hours.text), float(grade.text)]
              for hours, grade in zip(hist[2::7], hist[3::7])]

    return grades


def get_current(browser):
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/"
    browser.open(url)

    mirror = browser.find_all(class_="rich-table-cell ")
    current = [i.text for i in mirror if "id2" in str(i)]
    disciplines = [[name, int(hours)*18] for name, hours in
                   zip(current[3::10], current[5::10]) if int(hours)]

    return disciplines


def round_ufsc(grade):
    decimal = grade % 1
    if decimal < .25:
        return float(int(grade))
    if (.25 <= decimal < .75):
        return float(int(grade) + 0.5)
    if decimal >= .75:
        return float(int(grade) + 1)


def ia_calc(grades):
    def sumproduct(lists):
        return sum(reduce(mul, data) for data in lists)

    return round(sumproduct(grades) / sum(i[0] for i in grades), 2)


def iaa_poss(history, current):
    return (ia_calc(history + [[i[1], j] for i in current]) for j in [0, 10])


browser = login(input("Insira sua matrícula: "),
                getpass("Insira sua senha do CAGR: "))

student = get_student(browser)
history, current = get_history(browser), get_current(browser)

print("Olá, {}! Seu IAA é {}.".format(student, ia_calc(history)))

var = input("Deseja saber quanto seu IAA pode variar neste semestre? [s/N]: ")
if var.lower() == "s":
    print("Seu IAA pode variar de {} a {}."
          .format(*iaa_poss(history, current)))

for name, hours in current:
    while True:
        try:
            grade = float(input("Possível nota em {}: ".format(name)))
            if not (0 <= grade <= 10):
                raise ValueError
            break
        except ValueError:
            print("Nota inválida.")
    history.append([hours, round_ufsc(grade)])

iaa = ia_calc(history)
ia = ia_calc(history[-len(current):])
iap = ia_calc([i for i in history if i[1] >= 6])

print("Com as notas informadas, suas métricas serão:\n"
      "IAA: \033[1m{}\033[0m \t IA: {} \t IAP: {}".format(iaa, ia, iap))
