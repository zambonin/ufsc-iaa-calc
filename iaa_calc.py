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
    cls = "rich-table-cell"
    browser.open(url)

    cur = browser.find_all(class_=cls, id=re.compile("id2"))
    names = [n.text for n, c in zip(cur[4::10], cur[5::10]) if c.text]

    if not names:
        cur = browser.find_all(class_=cls, id=re.compile("id15"))
        names = [n.text for n, c in zip(cur[8::9], cur[::9]) if c.text == '1']

    return names


def round_ufsc(grade):
    decimal = grade % 1
    if decimal < .25:
        return float(int(grade))
    if .25 <= decimal < .75:
        return float(int(grade) + 0.5)
    if decimal >= .75:
        return float(int(grade) + 1)


def ia_calc(grades):
    def sumproduct(lists):
        return sum(reduce(mul, data) for data in lists)

    return sumproduct(grades) / sum(i[0] for i in grades)


def print_indexes(indexes):
    i = list(map(lambda x: str(x)[:4], indexes))
    return "\nIAA: \033[1m{}\033[0m \t IA: {} \t IAP: {}".format(*i)


def loop_input(msg, _type, cond):
    while True:
        try:
            var = _type(input(msg))
            if cond(var):
                raise ValueError
            return var
        except ValueError:
            pass


def get_input(student, current):
    new_history = student['grades'][:]

    for name in current:
        grade = loop_input("Possível nota em {}: ".format(name),
                           float, lambda x: not 0 <= x <= 10)
        hours = loop_input("Seu número de créditos: ",
                           int, lambda x: x < 0)
        new_history.append([hours * 18, round_ufsc(grade)])

    new_indexes = list(map(ia_calc, [
        new_history,
        new_history[-len(current):],
        list(filter(lambda x: x[1] >= 6, new_history))
    ]))

    print("Com as notas informadas, seus índices serão: {}".format(
        print_indexes(new_indexes)))

    return lambda x: x and get_input(student, current)


def main():
    browser = login(input("Insira sua matrícula: "),
                    getpass("Insira sua senha do CAGR: "))

    student, current = get_student_data(browser), get_current(browser)

    print("Olá, {}! Seus índices são: {}".format(
        student['name'], print_indexes(student['indexes'])))

    loop_input("ENTER para sair, digite algo para novo cálculo: ",
               bool, get_input(student, current))


if __name__ == '__main__':
    main()
