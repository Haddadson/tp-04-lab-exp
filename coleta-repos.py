import os
import sys
import time
from datetime import datetime
from json import dump, loads

import requests
from dateutil import relativedelta

# Execução da query para listagem de dados do GitHub


def run_query(json, headers):
    print("Executando query...")
    request = requests.post(
        'https://api.github.com/graphql', json=json, headers=headers)

    while (request.status_code != 200):
        print("Erro ao chamar API, tentando novamente...")
        print("Query failed to run by returning code of {}. {}. {}".format(
            request.status_code, json['query'], json['variables']))
        time.sleep(2)
        request = requests.post(
            'https://api.github.com/graphql', json=json, headers=headers)

    return request.json()


query = """
query laboratorio {
 search (query:"stars:>1000 topic:machine-learning sort:stars", type:REPOSITORY, first:20{AFTER}) {
    pageInfo{
        hasNextPage
        endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        url
        stargazers{
          totalCount
        }
        primaryLanguage{
          name
        }
        issues (first: 50) {
          totalCount
          nodes{
            createdAt
            updatedAt
            closedAt
            state
            title
            number
            url
            comments{
              totalCount
            }
          }
        }
        closedIssues: issues(states:CLOSED){
          totalCount
        }
        openIssues: issues(states:OPEN){
          totalCount
        }
      }
    }
  }
}
"""

# Chave de autenticação do GitHub
# Substitua o None por uma string com seu token de acesso ao GitHub

token_github = None  # INSIRA SEU TOKEN DO GITHUB AQUI #

if token_github is None:
    raise Exception("O token do GitHub não está configurado.")

headers = {"Authorization": "Bearer " + token_github}

# Efetua a mineração de dados do GitHub para obter dataset de repositórios


def mine_data():

    print("Minerando dados")

    final_query = query.replace("{AFTER}", "")

    json = {
        "query": final_query, "variables": {}
    }

    total_pages = 1

    print("Pagina -> 1")
    result = run_query(json, headers)

    nodes = result['data']['search']['nodes']
    next_page = result["data"]["search"]["pageInfo"]["hasNextPage"]

    # Paginação na consulta para listar os 100 repositórios
    while (next_page and total_pages < 5):
        total_pages += 1
        print("Pagina -> ", total_pages)
        cursor = result["data"]["search"]["pageInfo"]["endCursor"]
        next_query = query.replace("{AFTER}", ", after: \"%s\"" % cursor)
        json["query"] = next_query
        result = run_query(json, headers)
        nodes += result['data']['search']['nodes']
        next_page = result["data"]["search"]["pageInfo"]["hasNextPage"]

    print("Gravando cabeçalho do CSV de dados dos repositórios...")
    with open(sys.path[0] + "\\DadosRepositorios.csv", 'a+', encoding='utf-8') as repositories_file:
        repositories_file.write(
            "Título do Projeto" + ";" +
            "Data de criacao" + ";" +
            "Estrelas" + ";" +
            "Linguagem principal" + ";" +
            "Total de Issues" + ";" +
            "Total de Issues Abertas" + ";" +
            "Total de Issues Fechadas" + ";" +
            # "Mediana de comentários em issues" + ";" +
            "URL do repositorio" + "\n"
        )

    # Gravando cabeçalho do CSV de dados das issues...
    print("Gravando cabeçalho do CSV de dados das issues...")
    with open(sys.path[0] + "\\DadosIssues.csv", 'a+', encoding='utf-8') as issues_file:
        issues_file.write(
            "Titulo do Projeto" + ";" +
            "Titulo da Issue" + ";" +
            "ID" + ";" +
            "Total de comentarios" + ";" +
            "Estado" + ";" +
            "Data de criacao" + ";" +
            "Data de atualizacao" + ";" +
            "Data de conclusao" + ";" +
            "URL da issue" + "\n"
        )

    # Iterando dados retornados
    print("Iterando dados retornados...")
    for node in nodes:

        # Tratamento de dados para análise das métricas
        if node['primaryLanguage'] is None:
            primary_language = "None"
        else:
            primary_language = str(node['primaryLanguage']['name'])

        date_pattern = "%Y-%m-%dT%H:%M:%SZ"
        datetime_created_at = datetime.strptime(
            node['createdAt'], date_pattern)

        # Gravando dados dos repositórios no CSV
        with open(sys.path[0] + "\\DadosRepositorios.csv", 'a+', encoding='utf-8') as repositories_file:
            repositories_file.write(
                node['nameWithOwner'] + ";" +
                datetime_created_at.strftime('%d/%m/%y %H:%M:%S') + ";" +
                str(node['stargazers']['totalCount']) + ";" +
                primary_language + ";" +
                str(node['issues']['totalCount']) + ";" +
                str(node['openIssues']['totalCount']) + ";" +
                str(node['closedIssues']['totalCount']) + ";" +
                node['url'] + "\n"
            )

        print("\n ------ Repositorio gravado em CSV ------ \n")
        issues_nodes = node['issues']['nodes']

        # Itera issues do repositório para obter métricas

        for issue_node in issues_nodes:
            datetime_issue_created_at = datetime.strptime(
                issue_node['createdAt'], date_pattern)
            datetime_issue_updated_at = datetime.strptime(
                issue_node['updatedAt'], date_pattern)

            if(issue_node['closedAt'] is not None):
                datetime_issue_closed_at = datetime.strptime(
                    issue_node['closedAt'], date_pattern)
                closed_at_date = datetime_issue_closed_at.strftime(
                    '%d/%m/%y %H:%M:%S')
            else:
                closed_at_date = 'None'

            # Gravando dados da issue do repositório no CSV
            try:
                with open(sys.path[0] + "\\DadosIssues.csv", 'a+', encoding='utf-8') as issues_file:
                    issues_file.write(
                        node['nameWithOwner'] + ";" +
                        issue_node['title'] + ";" +
                        str(issue_node['number']) + ";" +
                        str(issue_node['comments']['totalCount']) + ";" +
                        issue_node['state'] + ";" +
                        datetime_issue_created_at.strftime('%d/%m/%y %H:%M:%S') + ";" +
                        datetime_issue_updated_at.strftime('%d/%m/%y %H:%M:%S') + ";" +
                        closed_at_date + ";" +
                        issue_node['url'] + "\n"
                    )
            except Exception as ex:
                print("Erro ao gravar: " + ex)
                print("Pulando repositorio")

    print("Finalizando...")


# Inicia mineração dos dados dos repositórios
mine_data()
