# emprego-moz-robot

Sistema automático de recolha e classificação de vagas de emprego em Moçambique.

## Ver as vagas

As vagas recolhidas estão disponíveis, actualizadas automaticamente todos os dias às 05h00, em:

**https://brevemito.github.io/emprego-moz-robot/**

A página permite filtrar por categoria e localização e ordenar por mais recentes ou mais relevantes. As mesmas vagas são também publicadas em [brevemito.com](https://mistyrose-ostrich-482714.hostingersite.com/emprego/).

## O que é

Um robot que percorre diariamente cerca de 21 fontes moçambicanas (portais de emprego, empresas, bancos e organizações internacionais) e reúne as vagas activas numa única lista, sem intervenção manual.

## Como funciona

- Scripts em Python, na pasta `scraper/`, percorrem cada fonte e extraem as vagas (um script dedicado por fonte, por exemplo BCI, ENH e Millennium BIM).
- Os dados recolhidos ficam guardados na pasta `data/`.
- Um workflow do GitHub Actions, na pasta `.github/workflows/`, corre automaticamente todos os dias às 05h00.
- O resultado é publicado como página estática através do GitHub Pages (o link acima).

## Estrutura do repositório

- `scraper/`: scripts de recolha, um por fonte
- `data/`: ficheiros com as vagas já recolhidas e tratadas
- `.github/workflows/`: automação que executa o robot diariamente
- `requirements.txt`: dependências Python do projecto (requests, beautifulsoup4, pandas)
