import dateparser
from datetime import datetime
from stackapi import StackAPI
from csv import DictReader
import requests
import sys
from json import dump, loads
import time

fieldnames = ["Titulo do Projeto", "Titulo da Issue", "ID", "Total de comentarios",
              "Estado", "Data de criacao", "Data de atualizacao", "Data de conclusao", "URL da issue"]


def issues():
    with open("DadosIssues.csv", "r") as file:
        for repo in DictReader(file, fieldnames, delimiter=";"):
            if(repo[fieldnames[0]] == fieldnames[0]):
                continue
            yield repo


def call(nameWithOwner, issue):
    try:
        request = requests.get(
            f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody")
        while (request.status_code != 200):
            print("Erro ao chamar API, tentando novamente...")
            print("Query failed to run by returning code of {}".format(
                request.status_code))
            time.sleep(5)
            request = requests.get(
                f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody")

        return request.json()

    except Exception as e:
        print(e)
    return None

# tags, owner,


def get_issues():
    with open(sys.path[0] + "\\DadosPerguntas.csv", 'a+', encoding='utf-8') as issues_file:
        issues_file.write(
            "Titulo do Projeto" + ";" +
            "ID Issue" + ";" +
            "Total Perguntas" + ";" +
            "Total Respostas" + ";" +
            "Total Respostas/Total Perguntas" + ";" +
            "Total perguntas apos issue" + ";" +
            "Pergunta criada primeiro em" + "\n"
        )
    for issue in issues():
        total_respostas = 0
        total_perguntas = 0
        total_perguntas_apos_issue = 0
        total_perguntas_antes_issue = 0
        issue_fechada_apos_resposta = 0

        if(issue["Titulo do Projeto"] is not None and issue["ID"] is not None):
            result = call(issue["Titulo do Projeto"], issue["ID"])
            total_perguntas += len(result["items"])

            for pergunta in result["items"]:
                total_respostas += pergunta["answer_count"]
                issue_created_at = dateparser.parse(issue['Data de criacao'])
                if(issue["Estado"] == "CLOSED"):
                    issue_closed_at = dateparser.parse(issue['Data de conclusao'])
                else:
                    issue_closed_at = None

                question_created_at = datetime.fromtimestamp(
                    pergunta["creation_date"])

                if(pergunta["is_answered"]):
                    question_answered_at = datetime.fromtimestamp(
                        pergunta["last_activity_date"])
                else:
                    question_answered_at = None

                if(issue_closed_at is not None and question_answered_at is not None):
                    dif = issue_closed_at - question_answered_at
                    if(dif.days <= 7):
                        issue_fechada_apos_resposta += 1


get_issues()
