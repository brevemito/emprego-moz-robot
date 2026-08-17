# Análise de Erros - emprego-moz-robot

## Problema Identificado

O scraper estava capturando **lixo (garbage)** em vez de vagas reais de emprego. Das 222 vagas inseridas, aproximadamente **95% eram inválidas**, incluindo:

### Exemplos de Lixo Capturado

**De TotalEnergies (8 vagas, ~7 inválidas):**
- "TotalEnergies Binding Corporate Rules"
- "Acessibilidade: parcialmente conforme"
- "Compromisso de Gestão Sócio-Ambiental"
- "Nossos compromissos"
- "Sustentabilidade"
- "Relatório & Contas"

**De BCI (33 vagas, ~30 inválidas):**
- "Código de Conduta do BCI"
- "Pedir um Financiamento"
- "Escolher um Cartão"
- "Aderir ao eBanking"
- "Reactivar o eBanking"
- "Comprar um Imóvel"
- "Actualização de Dados"
- "Aderir a um Seguro"
- "Condições de Utilização"
- "Responsabilidade Social"

**De Vodacom (10 vagas, ~9 inválidas):**
- "Vodafone Group Careers"
- "Asia-Pac Middle East"
- "Find out more Opens a new tab"
- Locais de trabalho (Maputo, Chimoio, etc.) formatados como vagas

## Causa Raiz

Os parsers usavam `soup.find_all("a")` para capturar TODOS os links da página, sem distinção entre:
- Links de navegação do site
- Links de política/privacidade
- Textos de marketing
- Vagas reais de emprego

### Problemas Específicos de Cada Parser:

1. **TotalEnergies**:
   - Threshold mínimo de 15 caracteres (muito baixo)
   - Filtro de lixo com apenas 8 palavras
   - Capturava qualquer `<a>` com mais de 15 caracteres

2. **BCI**:
   - Threshold mínimo de 10 caracteres (muito baixo)
   - Filtro de lixo com apenas 10 palavras
   - Capturava navegação, seções de conta, financiamento

3. **Vodacom**:
   - Threshold mínimo de 10 caracteres (muito baixo)
   - Filtro de lixo com apenas 9 palavras
   - Misturava títulos de trabalho com nomes de cidades/organizações

## Solução Implementada

### 1. Aumentar Threshold Mínimo para 20 Caracteres
```python
# ANTES: if len(title) < 10 ou < 15
# DEPOIS: if len(title) < 20
```

Um título de vaga típica tem pelo menos 20 caracteres:
- ✅ "Project Analyst-Resilient Water Supply" (40 chars)
- ✅ "National Consultant for Legal Environment" (42 chars)
- ❌ "Maputo, Mozambique" (17 chars) - REJEITADO

### 2. Expandir Lista de Palavras-Chave de Lixo

**Adicionadas ~50 palavras-chave:**
- Navegação: "pular para", "skip to", "onde", "onde estamos"
- Serviços bancários: "financiamento", "seguro", "cartão", "ebanking", "imóvel", "contas à ordem"
- Seções do site: "política", "privacidade", "condições", "termos", "responsabilidade", "código de conduta"
- Páginas corporativas: "relatório", "estrutura", "accionista", "negócio", "sustentabilidade"
- Idiomas: "português", "english", "moçambique"
- Marketing: "nossa", "nosso", "nossos", "página inicial", "negócio principal"

### 3. Reorganizar Lógica de Filtragem

```python
# NOVO FLUXO:
1. Extrair texto do link
2. Verificar comprimento >= 20 caracteres
3. Verificar se contém palavras de lixo
4. Validar URL
5. Verificar duplicação
```

## Resultados Esperados

Após aplicar estas correções, o próximo run deve:

- ✅ Reduzir vagas de BCI de 33 para ~1-3 reais
- ✅ Reduzir vagas de TotalEnergies de 8 para ~0-1 reais
- ✅ Reduzir vagas de Vodacom de 10 para ~2-5 reais
- ✅ Aumentar qualidade geral das vagas capturadas
- ✅ Manter vagas reais de fontes como UNJOBS, UN Moçambique, etc.

## Arquivos Modificados

1. `scraper/parsers/bci.py`
   - Aumentar threshold: 10 → 20 caracteres
   - Adicionar 45 palavras-chave ao filtro

2. `scraper/parsers/totalenergies.py`
   - Aumentar threshold: 15 → 20 caracteres
   - Adicionar 40 palavras-chave ao filtro

3. `scraper/parsers/vodacom_mz.py`
   - Aumentar threshold: 10 → 20 caracteres
   - Adicionar 35 palavras-chave ao filtro

## Próximos Passos

1. ✅ Executar `python scraper/main.py` novamente
2. ✅ Verificar qualidade das vagas capturadas
3. ⚠️ Se ainda houver lixo, adicionar mais palavras ao filtro
4. ⚠️ Considerar parsers mais específicos (ex: selectors CSS) para estas fontes

## Status das Outras Fontes

| Fonte | Status | Ação |
|-------|--------|------|
| emprego_co_mz | ✅ Bom | Nenhuma |
| contact_mz | ✅ Bom | Nenhuma |
| unjobs | ✅ Excelente | Nenhuma |
| un_mozambique | ✅ Excelente | Nenhuma |
| reliefweb | ⚠️ Sem vagas | Investigar ou remover |
| absa | ⚠️ Sem vagas | Investigar API Workday |
| mozparks, heineken, cim, bni, moza_banco, crowe | ⚠️ Sem parser | Criar parsers |
| tmcel | ❌ Erro rede | Verificar conectividade |
