#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W1632

"""iaa_calc.py

A Python script that simulates performance indices of students from the
Federal University of Santa Catarina with arbitrary final grades for the
courses they have taken, scraping the university's internal management
system for these informations.

    * `robobrowser.RoboBrowser` is a browser that can interact with web pages
        in various ways, such as clicking in buttons or submitting forms.
"""

from __future__ import absolute_import, division
from re import compile as _compile
from getpass import getpass

from robobrowser import RoboBrowser


def login(user, passwd):
    """
    Submits a login form to the university's systems.

    Args:
        user:   a string representing the user's email, university enrollment
                identifier, passport identifier, CPF (Individual Taxpayer
                Registration) or university identifier.
        passwd: a string representing a password for the user above.

    Returns:
        A RoboBrowser instance with a logged user.
    """
    browser = RoboBrowser(history=True, parser="html.parser")
    browser.open("https://sistemas.ufsc.br/login")

    form = browser.get_form(id="fm1")
    form["username"].value = user
    form["password"].value = passwd
    browser.submit_form(form)

    return browser


def get_student_data(browser):
    """
    Scrapes the student's history page for past grades.

    Args:
        browser:    a RoboBrowser instance with a logged in user.

    Returns:
        A dictionary consisting of the student's name, a matrix of grades
        and their respective quantity of credits and the student's current
        performance indices.

    Raises:
        SystemExit: in the case of a wrong password or
        if the system is not available.
    """
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/historicoEscolar/"
    browser.open(url)

    if "collecta" in browser.url:
        browser.submit_form(browser.get_form(id="j_id20"))

    if browser.url != url:
        raise SystemExit("Falha de autenticação!")

    hist = browser.find_all(class_="rich-table-cell ")

    if hist[1::7][-1].text == "FORMADO":
        raise SystemExit("Usuário já formado.")

    grades = [
        [int(hours.text), float(grade.text)]
        for hours, grade in zip(hist[2::7], hist[3::7])
        if hours.text
    ]

    try:
        base = "disciplina_footer_col{}"
        indexes = [
            browser.find_all(class_=base.format(i))[-1].text for i in [4, 2, 6]
        ]
    except IndexError:
        raise SystemExit("CAGR indisponível.")

    return {
        "name": browser.find(class_="rich-panel-header ").text,
        "grades": grades,
        "indexes": indexes,
    }


def get_current(browser):
    """
    Scrapes the student's current classes page for their names.

    Args:
        browser:    a RoboBrowser instance with a logged in user.

    Returns:
        A list with the student's current classes names.
    """
    url = "https://cagr.sistemas.ufsc.br/modules/aluno/espelhoMatricula/"
    cls = "rich-table-cell"
    browser.open(url)

    cur = browser.find_all(class_=cls, id=_compile("id2"))
    classes = [
        (n.text, int(c.text))
        for n, c in zip(cur[3::10], cur[5::10])
        if len(c.text)
    ]

    if not classes:
        cur = browser.find_all(class_=cls, id=_compile("id15"))
        classes = [
            (n.text, int(h.text))
            for n, h, c in zip(cur[8::9], cur[4::9], cur[5::9])
            if "_" not in c.text
        ]

    return classes


def round_ufsc(grade):
    """
    Rounds indices according to the university's rule
    (R17/CUn/97, Art. 71, §1).

    Args:
        grade:  float representing the index.

    Returns:
        A rounded float that can only end in 0.0 or 0.5.
    """
    decimal = grade % 1
    if decimal < 0.25:
        return float(int(grade))
    if 0.25 <= decimal < 0.75:
        return float(int(grade) + 0.5)
    return float(int(grade) + 1)


def ia_calc(grades):
    """
    Calculates the accumulated indices according to the university's rule
    (R17/CUn/97, Art. 43, I).

    Args:
        grades: a list of pairs, each one consisting of a grade from 0 to 10
                and the number of hours for the class.

    Returns:
        A float representing the weighted mean of the grades
        considering the number of hours for the classes.
    """
    return sum(h * g for h, g in grades) / sum(h for h, _ in grades)


def print_indexes(indexes):
    """Pretty-prints the three indices parsed from the student's page."""
    model = "\nIAA: \033[1m{}\033[0m \t IA: {} \t IAP: {}"
    return model.format(*list(map(lambda x: str(x)[:4], indexes)))


def loop_input(msg, _type, cond):
    """
    Prevents input from being accepted if it does not meet certain criteria.

    Args:
        msg:    a string containing the question for the input.
        _type:  a Python type or class.
        cond:   a function representing some restriction on the content
                of the variable.

    Returns:
        A variable of type `_type` that respects the conditions given.

    Raises:
        ValueError: if the cast or condition are not met, this is raised
                    to indicate that the user should input something else.
    """
    while True:
        try:
            var = _type(input(msg))
            if cond(var):
                raise ValueError
            return var
        except ValueError:
            pass


def get_input(student, current):
    """
    Queries the possible grades and how many credits each class has,
    calculating new indices with this information.

    Args:
        student:    a dictionary with information about a student's grades.
        current:    list of current classes a student is taking.

    Returns:
        An identity function and a new call of the function so the user can
        calculate multiple possibilities of indices using `loop_input`.
    """
    new_history = student["grades"][:]

    for name, hours in current:
        grade = loop_input(
            "Possível nota em {}: ".format(name),
            float,
            lambda x: not 0 <= x <= 10,
        )
        if not hours:
            hours = loop_input("Seu número de créditos: ", int, lambda x: x < 0)
        new_history.append([hours * 18, round_ufsc(grade)])

    new_indexes = list(
        map(
            ia_calc,
            [
                new_history,
                new_history[-len(current) :],
                list(filter(lambda x: x[1] >= 6, new_history)),
            ],
        )
    )

    print(
        "Com as notas informadas, seus índices serão: {}".format(
            print_indexes(new_indexes)
        )
    )

    return lambda x: x and get_input(student, current)


def main():
    """
    Logins the user, presents their current indices and asks for a preview
    of grades for this semester's classes, showing new indices thereafter.
    """
    browser = login(
        input("Insira sua matrícula ou idUFSC: "),
        getpass("Insira sua senha do CAGR: "),
    )

    student, current = get_student_data(browser), get_current(browser)

    print(
        "Olá, {}! Seus índices são: {}".format(
            student["name"], print_indexes(student["indexes"])
        )
    )

    loop_input(
        "ENTER para sair, digite algo para novo cálculo: ",
        bool,
        get_input(student, current),
    )


if __name__ == "__main__":
    main()
