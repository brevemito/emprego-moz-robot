# Lista de fontes de vagas em Moçambique

SOURCES = [

    # =========================
    # PORTAIS DE EMPREGO
    # =========================

    {
        "name": "emprego_co_mz",
        "url": "https://www.emprego.co.mz"
    },

        {
        "name": "contact_mz",
        # A página inicial deixou de listar vagas (dava 0 resultados).
        # Lista oficial de ofertas da CONTACT (agência licenciada pelo
        # INEP, com muitas vagas de nível médio e de entrada).
        "url": "https://www.contact.co.mz/pt/recrutamento/ofertas-de-emprego"
    },

    # =========================
    # EMPRESAS
    # =========================

    # ENERGIA / OIL & GAS
    {
        "name": "totalenergies",
        # Substituída a homepage (SPA, 0 resultados) pela página de
        # resultados de pesquisa, que é renderizada no servidor.
        # jobRecordsPerPage alto para tentar capturar tudo numa só página.
        "url": "https://jobs.totalenergies.com/en_US/careers/SearchJobs/Mozambique/?listFilterMode=1&jobRecordsPerPage=100"
    },

    {
        "name": "mozambique_lng",
        # A página institucional não lista vagas próprias - tem um link
        # directo para o portal de vagas da TotalEnergies (operadora do
        # projecto), já filtrado por este projecto específico.
        "url": "https://jobs.totalenergies.com/en_US/careers/SearchJobs/?3834=%5B41601%5D&3834_format=3639&listFilterMode=1&jobRecordsPerPage=50"
    },
    {
        "name": "exxonmobil",
        # Portal Oracle HCM da ExxonMobil (projecto Rovuma LNG). O URL é a
        # API pública em JSON que a própria página de vagas usa; o parser
        # pagina e fica só com as vagas em Moçambique.
        "url": "https://fa-exmi-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber=CX_1,limit=25,offset=0,sortBy=POSTING_DATES_DESC"
    },

    {
        "name": "eni",
        # Portal Oracle HCM da Eni (Coral Sul FLNG), mesma API da
        # ExxonMobil. Não foi possível testar a partir do ambiente de
        # desenvolvimento (o servidor recusou a ligação); se falhar no
        # GitHub Actions aparece como erro no relatório, sem afectar as
        # outras fontes.
        "url": "https://jobs.eni.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber=CX_1004,limit=25,offset=0,sortBy=POSTING_DATES_DESC"
    },

    # SERVIÇOS PETROLÍFEROS
    {
        "name": "slb",
        # Página da lista de vagas: o parser lê dela a chave pública de
        # pesquisa e pesquisa as vagas com país = Mozambique.
        "url": "https://careers.slb.com/job-listing"
    },

    {
        "name": "halliburton",
        # Página da região "Europe & Sub-Saharan Africa", onde ficam as
        # vagas de Moçambique (o parser filtra pelo código MZ).
        "url": "https://jobs.halliburton.com/go/Europe-&-Sub-Saharan-Africa-%28ESSA%29/8411900/"
    },
    {
        "name": "enh",
        "url": "https://precrutamento.enh.co.mz/vagas"
    },

    # =========================
    # BANCOS
    # =========================

    {
        "name": "bci",
        "url": "https://www.bci.co.mz/recrutamento/"
    },

    {
        "name": "millennium_bim",
        "url": "https://www.millenniumbim.co.mz/pt/institucional/o-banco/carreira"
    },

    {
        "name": "bni",
        "url": "https://www.bni.co.mz/en/about-bni/careers/"
    },

    {
        "name": "moza_banco",
        # Subpágina dedicada a vagas activas, em vez da página genérica
        # de careers.
        "url": "https://www.mozabanco.co.mz/en/institutional/careers/vacancies"
    },

    {
        "name": "absa",
        # O parser faz o pedido POST à API Workday da Absa.
        # Este URL serve como URL inicial da fonte.
        "url": "https://absa.wd3.myworkdayjobs.com/ABSAcareersite"
    },

    # =========================
    # TELECOMUNICAÇÕES
    # =========================

    {
        "name": "vodacom_mz",
        # NOTA: continua a devolver 0 resultados - confirmámos que é uma
        # SPA (Eightfold/PCSX) sem HTML de vagas no GET inicial. Ver
        # comentário detalhado em parsers/vodacom_mz.py.
        "url": "https://jobs.vodafone.com/careers?domain=vodafone.com&location=Mozambique"
    },

    {
        "name": "tmcel",
        # INVESTIGAÇÃO: o domínio anterior (tmcel.co.mz) está errado/morto
        # (por isso o ConnectTimeout constante). O domínio real é
        # tmcel.mz, mas tanto o site institucional (www.tmcel.mz) como o
        # portal de recrutamento dedicado (recrutamento.tmcel.mz)
        # BLOQUEIAM explicitamente scraping via robots.txt. Respeitamos
        # essa política e não construímos parser para esta fonte -
        # mantém-se sem parser (SEM PARSER no relatório) até haver uma
        # via de acesso autorizada (ex.: API pública, se vierem a
        # disponibilizar uma).
        "url": "https://www.tmcel.mz/"
    },

    {
        "name": "movitel",
        "url": "https://www.movitel.co.mz/"
    },

    # =========================
    # INDÚSTRIA / FMCG
    # =========================

    {
        "name": "heineken_mz",
        # Listagem filtrada pela "operating company" de Moçambique
        # (Cervejas de Moçambique), renderizada no servidor.
        "url": "https://careers.theheinekencompany.com/Portugues/job-listing?operatings_company%5B0%5D=5099"
    },

    {
        "name": "cim",
        # "CIM" = Cimentos de Moçambique. O domínio anterior (cim.co.mz)
        # não corresponde à empresa e não tem vagas próprias - a CIM
        # publica vagas via emprego.co.mz (página de empregador).
        "url": "https://www.emprego.co.mz/empregador/cimentos-de-mocambique/"
    },

    {
        "name": "mozparks",
        "url": "https://mozparks.co.mz/careers/"
    },

    # =========================
    # CONSULTORIA / SERVIÇOS
    # =========================

    {
        "name": "crowe_mz",
        "url": "https://www.crowe.com/mz/en-gb/careers"
    },

    # =========================
    # LOGÍSTICA / TRANSPORTES
    # =========================

    {
        "name": "agl_transport",
        # RSS da AGL filtrado para Moçambique.
        # Rss_JobCountry=159 corresponde a Moçambique.
        "url": "https://acareerbyagl.talent-soft.com/handlers/offerRss.ashx?LCID=1036&Rss_JobCountry=159"
    },

    # =========================
    # ORGANIZAÇÕES INTERNACIONAIS
    # =========================

    {
        "name": "un_mozambique",
        "url": "https://mozambique.un.org/pt/jobs"
    },

    {
        "name": "reliefweb",
        # A página pública é renderizada em JS (0 resultados via GET simples).
        # Passámos a usar a API pública em JSON, filtrada por Moçambique.
        "url": "https://api.reliefweb.int/v2/jobs?appname=brevemito-emprego-moz-robot&filter[field]=country.iso3&filter[value]=MOZ&fields[include][]=title&fields[include][]=url&fields[include][]=url_alias&fields[include][]=source&fields[include][]=country&sort[]=date.created:desc&limit=30"
    },

    {
        "name": "unjobs",
        "url": "https://unjobs.org/duty_stations/mozambique"
    }

]
