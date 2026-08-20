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
        "url": "https://www.contact.co.mz"
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
        "url": "https://www.mozambiquelng.co.mz/opportunities/working-with-us/"
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
        "url": "https://www.mozabanco.co.mz/en/institutional/careers"
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
        "url": "https://www.tmcel.co.mz/"
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
        "url": "https://careers.theheinekencompany.com/Mozambique/"
    },

    {
        "name": "cim",
        "url": "https://www.cim.co.mz/careers"
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
