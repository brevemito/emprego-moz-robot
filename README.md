# emprego-moz-robot

Sistema automático de recolha e classificação de vagas de emprego em Moçambique.

## Ver as vagas

As vagas recolhidas estão disponíveis, actualizadas automaticamente todos os dias às 05h00, em:

**https://brevemito.github.io/emprego-moz-robot/**

A página permite filtrar por categoria e localização e ordenar por mais recentes ou mais relevantes. As mesmas vagas são também publicadas em [brevemito.com](https://mistyrose-ostrich-482714.hostingersite.com/emprego/).

## Bolsas de estudo

A mesma página tem um separador **Bolsas de estudo**, com bolsas internacionais a que candidatos moçambicanos podem concorrer, ordenadas pelo prazo mais próximo e filtráveis por nível (licenciatura, mestrado, doutoramento, MBA) e país de estudo. Link directo para o separador:

**https://brevemito.github.io/emprego-moz-robot/#bolsas**

- Recolha: `scraper/bolsas.py`, todos os dias, logo a seguir às vagas (fonte: lista de bolsas abertas a africanos do [Scholars4Dev](https://www.scholars4dev.com)).
- Dados: `data/bolsas.json`.
- Programas em destaque (sempre no topo, mesmo sem edital aberto): `data/bolsas_fixas.json`. Inclui o PEC-PG, o GCUB-Mob, o PEC-G e a bolsa Study in Saudi. Para acrescentar outro programa, edite esse ficheiro no GitHub.
- Bolsas com o prazo já passado saem sozinhas. Se a fonte falhar, a lista anterior mantém-se, e as vagas são publicadas na mesma.
- Correr localmente: `python scraper/bolsas.py`

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
