# emprego-moz-robot

Sistema automático de recolha, validação e classificação de vagas de
emprego em Moçambique, a partir de 21 fontes diferentes (portais de
emprego, empresas, bancos, telecomunicações, organizações
internacionais). O resultado final é `data/jobs.json`, pronto a ser
consumido directamente pelo site **brevemito.com**.

## Índice

- [Como funciona](#como-funciona)
- [Fontes](#fontes)
- [Formato de `jobs.json`](#formato-de-jobsjson)
- [Como correr](#como-correr)
- [Automação (GitHub Actions)](#automação-github-actions)
- [Estrutura do projecto](#estrutura-do-projecto)
- [Limitações conhecidas](#limitações-conhecidas)
- [Adicionar uma nova fonte](#adicionar-uma-nova-fonte)
- [Manutenção](#manutenção)

## Como funciona

Cada execução (`scraper/main.py`) segue este fluxo:

```
1. Para cada fonte em scraper/sources.py:
   -> pedido HTTP (2 tentativas, com espera entre elas)
   -> o parser dessa fonte (scraper/parsers/<nome>.py) extrai candidatos

2. Para cada candidato extraído:
   -> normalização (espaços, travessões)
   -> validação estrutural (scraper/job_validator.py)
      - REJEITA se não houver evidência de ser uma vaga real
      - motivo de rejeição é guardado (navigation, procurement,
        institutional_page, category, search_filter, etc.)
   -> se válido:
      - título passa por limpeza de apresentação (scraper/text_cleanup.py)
        (Title Case, preservando siglas como M/F, HSE, QHSE, TI)
      - localização é melhorada quando possível (extrai província/cidade
        mencionada no título/descrição, em vez de "Moçambique" genérico)
      - pontuação de relevância (scraper/scoring.py)

3. Vagas válidas são guardadas na base de dados (SQLite, scraper/database.py)
   -> deduplicação automática (mesma vaga não é inserida duas vezes)

4. Exportação para data/jobs.json (scraper/export_json.py)
   -> adiciona job_id, category (scraper/job_category.py), localizações
      em lista, datas em formato ISO 8601
```

### Validação estrutural (não é uma lista negra)

`scraper/job_validator.py` **não** funciona por lista de palavras
proibidas. Em vez disso, exige **evidência positiva** de que um item é
mesmo uma vaga:

- o título contém um cargo reconhecível (`gestor`, `officer`,
  `motorista`, `engineer`, etc. - lista extensa em PT/EN, incluindo
  plurais), **ou**
- o URL segue um padrão conhecido de página de detalhe de vaga
  (`/vaga/`, `/vacancies/`, `/JobDetail/`, etc.)

Só depois disso é que a pontuação de relevância (`scoring.py`) entra em
jogo. Um domínio de confiança (ex.: site de um banco conhecido) nunca é
suficiente, por si só, para tornar uma página institucional válida.

Isto substituiu uma abordagem anterior de lista negra de palavras, que
era frágil e deixava passar muito lixo (relatórios anuais, páginas de
produtos bancários, filtros de menu, concursos públicos/RFP). Ver
`docs/ANALISE_ERROS.md` para o histórico dessa primeira tentativa
(hoje desactualizada).

## Fontes

21 fontes configuradas em `scraper/sources.py`. Nem todas produzem
vagas em todos os momentos - isso é normal, reflecte o que está
realmente publicado em cada site nesse instante.

| Fonte | Tipo de extracção | Notas |
|---|---|---|
| `emprego_co_mz` | URL de detalhe (`/vaga/`) | Portal de emprego |
| `contact_mz` | URL de detalhe (`oferta-de-emprego`) | Portal de emprego |
| `totalenergies` | URL de detalhe + filtro de país no texto | Página de pesquisa renderizada no servidor |
| `mozambique_lng` | Igual ao totalenergies | Mesmo portal, filtrado pelo projecto; deduplicado automaticamente contra `totalenergies` |
| `enh` | Melhor esforço (JobValidator) | Sem padrão de URL fiável; frequentemente sem vagas abertas |
| `bci` | Melhor esforço | Página de candidatura espontânea |
| `millennium_bim` | Melhor esforço | Página de candidatura espontânea |
| `bni` | Melhor esforço | Página de candidatura espontânea |
| `moza_banco` | Melhor esforço | Subpágina de vagas activas |
| `absa` | API interna Workday (POST) | Paginado, filtra por localização |
| `vodacom_mz` | ⚠️ Não funcional | SPA (Eightfold), sem HTML de vagas no pedido inicial |
| `tmcel` | ❌ Sem parser (deliberado) | Domínios reais bloqueiam scraping via `robots.txt` |
| `movitel` | Melhor esforço | Sem portal de vagas estruturado |
| `heineken_mz` | URL de detalhe (`/job/`) | Listagem filtrada por empresa operacional |
| `cim` | URL de detalhe (`/vaga/`) | Cimentos de Moçambique, via emprego.co.mz |
| `mozparks` | Melhor esforço | Sem portal de vagas estruturado |
| `crowe_mz` | Melhor esforço | Sem portal de vagas estruturado |
| `agl_transport` | Feed RSS | Já filtrado por Moçambique na origem |
| `un_mozambique` | Melhor esforço | ONU e agências afiliadas |
| `reliefweb` | ⚠️ API bloqueada | Ver [Limitações conhecidas](#limitações-conhecidas) |
| `unjobs` | URL de detalhe (`/vacancies/`) | Fonte mais produtiva |

"Melhor esforço" significa: o parser recolhe todos os links da página
e deixa o `JobValidator` decidir o que é válido, porque não existe um
padrão de URL fiável de "detalhe de vaga" identificável nesse site.

## Formato de `jobs.json`

```json
{
  "job_id": "unjobs_7b01fda04b75",
  "title": "Motorista - Cabo Delgado",
  "company": "UN Jobs",
  "location": "Cabo Delgado, Pemba",
  "locations": ["Cabo Delgado", "Pemba"],
  "category": "Logística e Transportes",
  "description": null,
  "url": "https://unjobs.org/vacancies/...",
  "source": "unjobs",
  "score": 80,
  "scraped_at": "2026-08-23T12:14:33Z",
  "created_at": "2026-08-23 12:14:33"
}
```

| Campo | Descrição |
|---|---|
| `job_id` | Identificador estável, único por vaga |
| `title` | Título já limpo (Title Case, siglas preservadas) |
| `company` | Nome do empregador |
| `location` | Localização como texto (pode ter mais do que um local) |
| `locations` | A mesma informação, como lista, para filtrar por província/cidade |
| `category` | Uma de 13 categorias (`scraper/job_category.py`), ou `"Outros"` |
| `description` | Texto adicional à parte do título, ou `null` se não houver nenhum |
| `url` | Link para a vaga original |
| `source` | Nome interno da fonte (ver tabela acima) |
| `score` | Pontuação de relevância (0-100), usada para ordenar |
| `scraped_at` | Data/hora da recolha, em ISO 8601 (UTC) |
| `created_at` | Igual, no formato original do SQLite (mantido por compatibilidade) |

O ficheiro está ordenado por `score` decrescente.

## Como correr

```bash
git clone https://github.com/brevemito/emprego-moz-robot.git
cd emprego-moz-robot
pip install -r requirements.txt

cd scraper
python3 main.py
```

No final, o `data/jobs.json` fica actualizado, e a consola mostra um
relatório detalhado por fonte (quantos itens brutos, quantos válidos,
rejeitados por categoria, novos vs. duplicados) e exemplos de itens
rejeitados com o motivo.

**Nota:** a base de dados (`scraper/data/jobs.db`) é recriada do zero em
cada execução - não acumula histórico entre execuções separadas (ver
secção seguinte). A deduplicação só actua dentro da mesma execução
(ex.: quando a mesma vaga aparece em `totalenergies` e
`mozambique_lng`).

## Automação (GitHub Actions)

O workflow `.github/workflows/run.yml` corre:

- **Automaticamente**, todos os dias às 05:00 (hora de Moçambique).
- **Manualmente**, a qualquer momento, através da aba **Actions** do
  GitHub → workflow "Job Scraper Moçambique" → botão **"Run workflow"**.

No final de cada execução, o `data/jobs.json` é automaticamente
commitado e enviado (`git push`) para o repositório.

Como o `checkout` de cada execução é sempre limpo (não guarda a base de
dados entre execuções), cada run reflecte apenas o que está realmente
publicado nas fontes **nesse momento** - não é um arquivo cumulativo de
tudo o que já alguma vez existiu.

## Estrutura do projecto

```
scraper/
  main.py              - ponto de entrada; orquestra tudo
  sources.py           - lista das 21 fontes (nome + URL)
  job_validator.py      - validação estrutural (vaga real vs. lixo)
  job_category.py       - categorização por área profissional
  text_cleanup.py       - limpeza de título e extracção de localização
  scoring.py            - pontuação de relevância
  database.py            - camada SQLite (inserção, deduplicação)
  export_json.py         - exportação final para data/jobs.json
  cleanup_database.py    - manutenção local (ver secção Manutenção)
  parsers/
    __init__.py           - registo de todos os parsers
    <fonte>.py             - um parser por fonte, um por ficheiro
data/
  jobs.json               - resultado final, consumido pelo site
docs/
  ANALISE_ERROS.md         - histórico da primeira tentativa de correcção (desactualizado)
.github/workflows/
  run.yml                  - automação (agendamento diário + manual)
```

## Limitações conhecidas

Estas não são bugs por corrigir no código - são restrições externas:

- **`reliefweb`**: a API pública do ReliefWeb passou a exigir, desde
  Novembro de 2025, um parâmetro `appname` **pré-aprovado** por eles.
  Sem essa aprovação, devolve sempre `403 Forbidden`. Para reactivar:
  pedir aprovação em https://reliefweb.int/contact (sugestão: usar o
  domínio `brevemito.com`) e depois actualizar o parâmetro `appname=`
  em `scraper/sources.py`.

- **`tmcel`**: tanto o site institucional (`www.tmcel.mz`) como o
  portal de recrutamento dedicado bloqueiam explicitamente scraping via
  `robots.txt`. Respeitamos essa política - esta fonte fica
  deliberadamente sem parser.

- **`vodacom_mz`**: o portal de carreiras corre sobre uma Single Page
  Application (Eightfold/PCSX) que não devolve vagas num pedido HTTP
  simples - só carrega o conteúdo via JavaScript depois. Resolver isto
  exigiria um browser headless (Playwright/Selenium), fora do âmbito
  actual deste projecto (baseado em `requests` + `BeautifulSoup`).

- **`bci`, `millennium_bim`, `bni`, `moza_banco`, `movitel`, `mozparks`,
  `crowe_mz`, `enh`**: não têm um portal de vagas estruturado com
  páginas de detalhe individuais - são sobretudo páginas de
  "candidatura espontânea". Estas fontes produzem 0 resultados na
  maior parte do tempo, o que é o comportamento correcto (não inventar
  vagas onde não existem); só aparecem resultados quando essas
  empresas publicam mesmo uma vaga com um título de cargo reconhecível
  nessas páginas.

## Adicionar uma nova fonte

1. Confirmar se a página de vagas é renderizada no servidor (testar com
   um pedido HTTP simples, sem JavaScript) ou se precisa de API.
2. Se houver um padrão de URL de "detalhe de vaga" (ex.: `/vaga/123`),
   usá-lo como evidência estrutural forte no parser (ver
   `parsers/emprego_co_mz.py` como exemplo).
3. Se não houver, escrever um parser "melhor esforço" que recolha todos
   os links e delegue a decisão ao `job_validator.classify()` (ver
   `parsers/millennium_bim.py` como exemplo).
4. Registar a nova fonte em `scraper/sources.py` e o novo parser em
   `scraper/parsers/__init__.py`.
5. Testar localmente (`python3 main.py`) e confirmar no relatório final
   que a fonte não está a produzir falsos positivos.

## Manutenção

`scraper/cleanup_database.py` remove vagas que já não passam no
`JobValidator` actual e reformata título/localização de vagas antigas,
mas só é útil se correr contra uma base de dados **local** que já
tenha acumulado histórico (ex.: testes feitos na sua máquina). Em
produção (GitHub Actions), a base de dados é sempre recriada do zero
em cada execução, por isso este script não tem efeito lá - não precisa
de ser corrido como parte do fluxo normal.
