# Financial Investments AI Bot

Este projeto é um sistema de análise de ações e avaliação de riscos de investimentos, utilizando agentes de IA para fornecer insights detalhados sobre o mercado, riscos e tendências de ações. A aplicação foi desenvolvida para permitir que investidores e analistas tenham acesso a informações de mercado atualizadas e possam avaliar o risco de forma eficiente.

## Funcionalidades

- **Análise de Ações**: Consulta de dados financeiros e técnicos de uma empresa por meio da integração com APIs, como Alpha Vantage e Yahoo Finance.
- **Avaliação de Riscos**: O agente `riskAnalyst` fornece uma análise detalhada dos riscos de investimento em uma empresa, considerando fatores de risco de mercado, operacionais, regulatórios e ESG.
- **Boletim Informativo**: O agente `stockAnalystWrite` escreve um relatório de três parágrafos sobre a análise de tendências de preços, riscos e notícias relevantes.
- **Pesquisa de Notícias**: Integração com a ferramenta DuckDuckGo Search para busca de notícias financeiras relevantes sobre as empresas.
- **Interface Interativa com Streamlit**: A aplicação conta com uma interface desenvolvida em Streamlit para exibir os resultados de pesquisa de forma clara e interativa.

## Tecnologias Utilizadas

- **Python**: Linguagem principal utilizada no projeto.
- **Streamlit**: Framework utilizado para criação da interface de usuário.
- **CrewAI**: Utilizado para orquestrar os agentes de IA responsáveis pelas análises e relatórios.
- **LangChain**: Framework utilizado para integrar os modelos de linguagem e gerenciar as correntes de tarefas dos agentes.
- **APIs**:
  - **Alpha Vantage**: Fornece dados financeiros e análises técnicas.
  - **Yahoo Finance**: Utilizado para acessar cotações e informações de mercado.
- **WSL (Windows Subsystem for Linux)**: Ambiente de desenvolvimento configurado com Ubuntu e Python 3.12.
- **DuckDuckGo Search**: Ferramenta utilizada para pesquisar notícias relacionadas à empresa alvo da análise.

## Estrutura do Projeto

- **Agentes de IA**:
  - `stockAnalystWrite`: Análise de tendências de preços e redação de um boletim informativo.
  - `riskAnalyst`: Avaliação dos riscos de investimento, levando em conta diversos fatores.
- **Funções Auxiliares**:
  - `fetch_stock_price`: Função que busca os preços de ações dentro de um intervalo de datas e retorna os dados formatados.
  - Integração com o Yahoo Finance para obter informações detalhadas de mercado.
  - Validação de datas e tratamento adequado para garantir a integridade dos dados de entrada.
