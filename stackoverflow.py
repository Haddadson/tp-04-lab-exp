import csv
import statistics
import sys
import time
from csv import DictReader
from datetime import datetime
from json import dump, loads

import dateparser
import requests
import statistics

def issues():
    issuesHeader = ["Titulo do Projeto", "Titulo da Issue", "ID", "Total de comentarios",
                    "Estado", "Data de criacao", "Data de atualizacao", "Data de conclusao", "URL da issue"]

    with open("DadosIssuesTeste.csv", "r") as file:
        for repo in DictReader(file, issuesHeader, delimiter=";"):
            if(repo[issuesHeader[0]] == issuesHeader[0]):
                continue
            yield repo


def call(nameWithOwner, issue):
    try:
        request = requests.get(
            f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody")
        # f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody&key=ddMUWlWLoVx1S031D4HRqA((")
        while (request.status_code != 200):
            print("Erro ao chamar API, tentando novamente...")
            print("Query failed to run by returning code of {}".format(
                request.status_code))
            time.sleep(5)
            request = requests.get(
                f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody")
            # f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=votes&q={nameWithOwner}/{issue}&site=stackoverflow&filter=withBody&key=ddMUWlWLoVx1S031D4HRqA((")

        return request.json()

    except Exception as e:
        print(e)
    return None


def set_repositories_data():
    data = {}
    with open("DadosRepositorios.csv", "r") as file:
        next(file)
        csv_data = csv.reader(file, delimiter=';')
        for repo in csv_data:
            data[repo[0]] = {
                'estrelas': (int(repo[2])), 'perguntas': 0, 'respostas': 0}
    return data


def main():
    # RQ1: Com que frequência issues do GitHub são discutidas no Stack Overflow?
    total_geral_perguntas = 0
    # RQ02: Qual o impacto das discussões de issues do GitHub no Stack Overflow?
    impacto_issues = 0
    # RQ03: Existe alguma relação entre a popularidade dos repositórios e o buzz gerado?
    dados_repositorios = set_repositories_data()
    # RQ04: Perguntas com respostas aceitas do SO relacionadas à issues do GitHub tendem a ter mais de uma resposta ?
    qtd_respostas_por_pergunta = []
    # RQ05: Issues relacionadas a perguntas são fechadas quando respostas são aceitas?
    issues_fechadas = 0
    issues_fechadas_apos_resposta = 0
    # RQ06: Os usuários costumam fazer perguntas no SO?
    issues_criadas_antes = 0
    issues_criadas_apos = 0
    total_perguntas_apos_issue = 0
    total_perguntas_antes_issue = 0

    total_geral_respostas = 0

    with open(sys.path[0] + "\\DadosPerguntas.csv", 'a+', encoding='utf-8') as issues_file:
        issues_file.write(
            "Titulo do Projeto;ID Issue;ID Pergunta;Titulo;Respondida;Respostas;Data da criação;Link;Tags\n"
            # "Titulo do Projeto" + ";" + "ID Issue" + ";" + "Total Perguntas" + ";" +
            # "Total Respostas" + ";" + "Total Respostas/Total Perguntas" + ";" +
            # "Total perguntas apos issue" + ";" + "Pergunta criada primeiro em" + "\n"
        )
        for issue in issues():

            data_criacao_issue = dateparser.parse(
                        issue['Data de criacao'])

            menor_data_criacao_pergunta = None

            if(issue["Titulo do Projeto"] is not None and issue["ID"] is not None):
                result = call(issue["Titulo do Projeto"], issue["ID"])

                total_geral_perguntas += len(result["items"])
                dados_repositorios[issue["Titulo do Projeto"]
                                   ]['perguntas'] += len(result["items"])

                for pergunta in result["items"]:
                    issues_file.write(
                        f"{issue['Titulo do Projeto']};{issue['ID']};{str(pergunta['question_id'])};{pergunta['title']};{str(pergunta['is_answered'])};{str(pergunta['answer_count'])};{str(dateparser.parse(str(pergunta['creation_date'])))};{pergunta['link']};{', '.join(pergunta['tags'])};\n")

                    total_geral_respostas += pergunta["answer_count"]
                    dados_repositorios[issue["Titulo do Projeto"]
                                       ]['respostas'] += pergunta["answer_count"]
                                       
                    pergunta_possui_resposta_aceita = 'accepted_answer_id' in pergunta

                    if(pergunta_possui_resposta_aceita and pergunta['accepted_answer_id'] is not None):
                        qtd_respostas_por_pergunta.append(pergunta['answer_count'])

                    if(issue["Estado"] == "CLOSED"):
                        issues_fechadas += 1
                        issue_closed_at = dateparser.parse(
                            issue['Data de conclusao'])
                    else:
                        issue_closed_at = None

                    question_created_at = datetime.fromtimestamp(
                        pergunta["creation_date"])

                    if(question_created_at < data_criacao_issue):
                        total_perguntas_antes_issue += 1
                    elif(question_created_at > data_criacao_issue):
                        total_perguntas_apos_issue += 1

                    if(menor_data_criacao_pergunta is None or question_created_at < menor_data_criacao_pergunta):
                        menor_data_criacao_pergunta = question_created_at

                    if(pergunta["is_answered"]):
                        question_answered_at = datetime.fromtimestamp(
                            pergunta["last_activity_date"])
                    else:
                        question_answered_at = None

                    if(issue_closed_at is not None and question_answered_at is not None):
                        dif = issue_closed_at - question_answered_at
                        if(dif.days <= 7):
                            issues_fechadas_apos_resposta += 1

                if(menor_data_criacao_pergunta is not None and menor_data_criacao_pergunta < data_criacao_issue):
                    issues_criadas_apos += 1
                elif(menor_data_criacao_pergunta is not None and menor_data_criacao_pergunta > data_criacao_issue):
                    issues_criadas_antes +=1

        #Sleep para evitar muitas chamadas na API do SO
        time.sleep(3)


    impacto_issues = total_geral_respostas / total_geral_perguntas

    # Gerando resultados RQ3:
    with open(sys.path[0] + "\\RQ3.csv", 'a+', encoding='utf-8') as rq3_file:
        rq3_file.write(
            "Titulo do Projeto" + ";" + "Perguntas" + ";" + "Respostas" + "\n")

        for repo in dados_repositorios:
            rq3_file.write(
                f"{repo};{dados_repositorios[repo]['perguntas']};{dados_repositorios[repo]['respostas']}\n")
    # Gerando resultados RQ5:
    issues_resolvidas_pelo_SO = (
        issues_fechadas_apos_resposta / issues_fechadas) * 100

    mediana_respostas = statistics.median(qtd_respostas_por_pergunta)

    print(f"RQ1: {total_geral_perguntas}")
    print(f"RQ2: {impacto_issues}")
    print(f"RQ3: resultados salvos em arquivo")
    print(f"RQ4: {mediana_respostas}")
    print(f"RQ5: {issues_resolvidas_pelo_SO}%")
    print(f"RQ6: Issues criadas antes das perguntas: {issues_criadas_antes}")
    print(f"RQ6: Issues criadas apos as perguntas: {issues_criadas_apos}")
    print(f"RQ6: Perguntas criadas antes das issues: {total_perguntas_antes_issue}")
    print(f"RQ6: Perguntas criadas apos as issues: {total_perguntas_apos_issue}")


if __name__ == "__main__":
    main()
