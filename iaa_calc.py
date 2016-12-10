#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

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


def get_student_data(browser):
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/historicoEscolar/"
    browser.open(url)

    if "collecta" in browser.url:
        browser.submit_form(browser.get_form(id="j_id20"))

    if browser.url != url:
        raise SystemExit("Falha de autenticação!")

    hist = browser.find_all(class_="rich-table-cell ")
    grades = [[int(hours.text), float(grade.text)]
              for hours, grade in zip(hist[2::7], hist[3::7])]

    try:
        indexes = [browser.find_all(class_="disciplina_footer_col{}"
                                    .format(i))[-1].text for i in [4, 2, 6]]
    except IndexError:
        raise SystemExit("CAGR indisponível.")

    return {
        'name': browser.find(class_="rich-panel-header ").text,
        'grades': grades,
        'indexes': indexes,
    }


def get_current(browser):
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/"
    browser.open(url)

    current = browser.find_all(class_="rich-table-cell", id=re.compile("id2"))
    return [name.text for name in current[3::10]]


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

    return sumproduct(grades) / sum(i[0] for i in grades)


def get_input(history, current):
    for name in current:
        while True:
            try:
                grade = float(input("Possível nota em {}: ".format(name)))
                if not (0 <= grade <= 10):
                    raise ValueError
                break
            except ValueError:
                print("Nota inválida.", end=' ')
        while True:
            try:
                hours = int(input("Seu número de créditos: "))
                if hours < 0:
                    raise ValueError
                break
            except ValueError:
                print("Entrada inválida.", end=' ')

        history.append([hours * 18, round_ufsc(grade)])

    return history


def print_indexes(indexes):
    i = list(map(lambda x: str(x)[:4], indexes))
    return "\nIAA: \033[1m{}\033[0m \t IA: {} \t IAP: {}".format(*i)


if __name__ == '__main__':
    browser = login(input("Insira sua matrícula: "),
                    getpass("Insira sua senha do CAGR: "))

    student, current = get_student_data(browser), get_current(browser)

    print("Olá, {}! Seus índices são: {}".format(
              student['name'], print_indexes(student['indexes'])))

    repeat = True
    while repeat:
        new_history = get_input(student['grades'][:], current)
        new_indexes = list(map(ia_calc, [
            new_history,
            new_history[-len(current):],
            list(filter(lambda x: x[1] >= 6, new_history))
        ]))

        print("Com as notas informadas, seus índices serão: {}".format(
            print_indexes(new_indexes)))

        repeat = bool(input("Digite algo para realizar um novo cálculo ou "
                            "aperte ENTER para sair: "))
