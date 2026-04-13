 ![Logo-IFPI-Vertical][image1]  
**INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO PIAUÍ**  
**CAMPUS PARNAÍBA**  
**CURSO TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS**

**CAUÃ WESLY SILVA ROCHA**  
**ELINNE PACHECO PESSOA**  
**FERNANDA OLIVEIRA DE FARIAS**  
**FRANCISCO JUNIO ALVES BARROS**  
**THIAGO CARVALHO DA SILVA**

**GESTHAR: SISTEMA DE PONTO DE VENDA E CONTROLE DE ESTOQUE PARA LOJA DE ROUPAS PARA GESTANTES**

**PARNAÍBA**  
**2025**   
CAUÃ WESLY SILVA ROCHA  
ELINNE PACHECO PESSOA  
FERNANDA OLIVEIRA DE FARIAS  
FRANCISCO JUNIO ALVES BARROS  
THIAGO CARVALHO DA SILVA

GESTHAR: SISTEMA DE PONTO DE VENDA E CONTROLE DE ESTOQUE PARA LOJA DE ROUPAS PARA GESTANTES

Projeto de extensão apresentado como exigência para aprovação na disciplina Extensão Curricular I do Curso de Tecnologia em Análise e Desenvolvimento de Sistemas do Instituto Federal de Educação, Ciência e Tecnologia do Piauí, Campus Parnaíba.

Orientador(a): Prof. Me. José Renato de Moura Silva Barroso.

PARNAÍBA  
2025  
**LISTA DE TABELAS**

| Tabela 1 | Requisitos Funcionais (RF) de Controle de Estoque………………… | 16 |
| :---- | :---- | :---: |
| Tabela 2 | Requisitos Funcionais (RF) de Cadastro de Usuários………………. | 17 |
| Tabela 3 | Requisitos Funcionais (RF) de Cadastro de Clientes…………...….. | 18 |
| Tabela 4 | Requisitos Funcionais (RF) de Ponto de Venda……………………… | 19 |
| Tabela 5 | Requisitos Funcionais (RF) de Relatórios…………………………….. | 20 |
| Tabela 6 | Requisitos Não Funcionais (RNF) de Usabilidade…………………… | 21 |
| Tabela 7 | Requisitos Não Funcionais (RNF) de Segurança……………………. | 22 |
| Tabela 8 | Requisitos Não Funcionais (RNF) de Compatibilidade……………… | 22 |
| Tabela 9 | Requisitos Não Funcionais (RNF) de Disponibilidade………………. | 22 |
| Tabela 10 | Requisitos Não Funcionais (RNF) de Equipamentos………………... | 23 |
| Tabela 11 | Requisitos Não Funcionais (RNF) de Serviços Externos…………… | 23 |
| Tabela 12 | Cronograma de Atividades Executadas............................................. | 39 |

**LISTA DE ABREVIATURAS E SIGLAS**

| ADS | Análise e Desenvolvimento de Sistemas |
| :---- | :---- |
| CEP | Código de Endereçamento Postal  |
| CNPJ | Cadastro Nacional da Pessoa Jurídica |
| CPF | Cadastro de Pessoas Físicas |
| CSS | Cascading Style Sheets |
| IFPI | Instituto Federal de Educação, Ciência e Tecnologia do Piauí  |
| MTV | Model-Template-View  |
| ORM | Object-Relational Mapping (Mapeamento Objeto-Relacional)  |
| PDCA | Plan-Do-Check-Act  |
| PDV | Ponto de Venda  |
| RF | Requisito Funcional |
| RNF | Requisito Não Funcional |
| SKU | Stock Keeping Unit (Unidade de Manutenção de Estoque)  |
| TADS | Tecnólogo em Análise e Desenvolvimento de Sistemas  |
| UML | Unified Modeling Language (Linguagem de Modelagem Unificada) |
| VPS | Virtual Private Server (Servidor Virtual Privado) |
| KANBAN | Metodologia Ágil de Desenvolvimento |

**SUMÁRIO**

[**1 INTRODUÇÃO	8**](#1-introdução)

[**2 JUSTIFICATIVA	10**](#2-justificativa)

[**3 OBJETIVOS	11**](#3-objetivos)

[3.1 OBJETIVO GERAL	11](#heading=)

[3.2 OBJETIVOS ESPECÍFICOS	11](#heading=)

[3.3 DIFERENCIAIS DO SISTEMA GESTHAR	11](#3.3-diferenciais-do-sistema-gesthar)

[3.3.1 ESPECIALIZAÇÃO PARA O NICHO DE MODA GESTANTE	11](#3.3.1-especialização-para-o-nicho-de-moda-gestante)

[3.3.2 ARQUITETURA PARA MICROEMPRESAS	12](#3.3.2-arquitetura-para-microempresas)

[3.3.3 AUTONOMIA OPERACIONAL E INTELIGÊNCIA DE NEGÓCIO	12](#3.3.3-autonomia-operacional-e-inteligência-de-negócio)

[3.3.4 INTEGRAÇÃO E SEGURANÇA	12](#3.3.4-integração-e-segurança)

[3.3.5 TECNOLOGIA ACESSÍVEL E SUSTENTÁVEL	13](#3.3.5-tecnologia-acessível-e-sustentável)

[**4 REFERENCIAL TEÓRICO	14**](#4-referencial-teórico)

[**5 RESULTADOS ALCANÇADOS (EXTENSÃO CURRICULAR I)	16**](#5-resultados-alcançados-\(extensão-curricular-i\))

[5.1 ANÁLISE E PLANEJAMENTO	16](#5.1-análise-e-planejamento)

[5.2 PROTOTIPAÇÃO DE TELAS	16](#5.2-prototipação-de-telas)

[5.3 CONFIGURAÇÃO DO AMBIENTE	16](#5.3-configuração-do-ambiente)

[5.4 MÓDULO DE PRODUTOS E CONTROLE DE ESTOQUE	16](#5.4-módulo-de-produtos-e-controle-de-estoque)

[5.5 MÓDULO DE PONTO DE VENDA (PDV)	17](#5.5-módulo-de-ponto-de-venda-\(pdv\))

[5.6 MÓDULOS DE USUÁRIOS E CLIENTES	17](#5.6-módulos-de-usuários-e-clientes)

[**6 METODOLOGIA DA EXECUÇÃO DO PROJETO	18**](#6-metodologia-da-execução-do-projeto)

[**7 ESPECIFICAÇÃO DO SISTEMA	19**](#7-especificação-do-sistema)

[7.1 LISTA DE REQUISITOS FUNCIONAIS	19](#7.1-lista-de-requisitos-funcionais)

[7.1.1 CONTROLE DE ESTOQUE	19](#7.1.1-controle-de-estoque)

[7.1.2 CADASTRO DE USUÁRIOS (FUNCIONÁRIOS)	20](#7.1.2-cadastro-de-usuários-\(funcionários\))

[7.1.3 CADASTRO DE CLIENTES	21](#7.1.3-cadastro-de-clientes)

[7.1.4 PONTO DE VENDA (PDV)	22](#7.1.4-ponto-de-venda-\(pdv\))

[7.1.5 RELATÓRIOS	23](#7.1.5-relatórios)

[7.2 LISTA DE REQUISITOS NÃO FUNCIONAIS	24](#7.2-lista-de-requisitos-não-funcionais)

[7.2.1 USABILIDADE	24](#7.2.1-usabilidade)

[7.2.2 SEGURANÇA	25](#7.2.2-segurança)

[7.2.3 COMPATIBILIDADE	25](#7.2.3-compatibilidade)

[7.2.4 DISPONIBILIDADE	25](#7.2.4-disponibilidade)

[7.2.5  EQUIPAMENTOS	26](#7.2.5-equipamentos)

[7.2.6 SERVIÇOS EXTERNOS	26](#7.2.6-serviços-externos)

[7.3 MODELAGEM E ARQUITETURA DO SISTEMA	27](#7.3-modelagem-e-arquitetura-do-sistema)

[7.4 PROTOTIPAÇÃO DE TELAS	27](#7.4-prototipação-de-telas)

[7.5 TECNOLOGIAS UTILIZADAS	27](#7.5-tecnologias-utilizadas)

[7.5.1 FIGMA	27](#7.5.1-figma)

[7.5.2 POSTGRESQL	28](#7.5.2-postgresql)

[7.5.3 DJANGO	28](#7.5.3-django)

[7.5.4 BOOTSTRAP	28](#7.5.4-bootstrap)

[**8 RESULTADOS ESPERADOS	29**](#8-resultados-esperados)

[**9 DISSEMINAÇÃO DOS RESULTADOS	30**](#9-disseminação-dos-resultados)

[**10 CRONOGRAMA DE EXECUÇÃO	39**](#10-cronograma-de-execução)

[**11 CONSIDERAÇÕES FINAIS	40**](#11-considerações-finais)

[**12 REFERÊNCIAS	41**](#12-referências)

[**APÊNDICE A \- DOCUMENTAÇÃO TÉCNICA E DIAGRAMAS DE SISTEMAS	42**](#apêndice-a---documentação-técnica-e-diagramas-de-sistemas)

[**APÊNDICE B \- PROTOTIPAÇÃO DE TELAS	45**](#apêndice-b---prototipação-de-telas)

[**APÊNDICE C \- TELAS DO SISTEMA IMPLEMENTADO	55**](#apêndice-c---telas-do-sistema-implementado)

# **1 INTRODUÇÃO** {#1-introdução}

Com a crescente expansão da utilização de sistemas de software como ferramentas facilitadoras para a gestão de empresas, a cada dia surgem novas oportunidades de aplicar a tecnologia a fim da melhoria de processos, aumento de vendas e eficiência no gerenciamento de estoques. Um exemplo comum disso, são os sistemas Ponto de Vendas (PDV), um tipo de sistema de gestão empresarial que facilita os procedimentos de venda na frente de loja.  
Nesse contexto, este projeto de extensão documenta o desenvolvimento de um sistema web chamado Gesthar para a loja Linda Gestante, uma empresa local que surgiu em 2018 e atua no segmento de vendas de roupas para gestantes e lactantes, possuindo apenas uma colaboradora \- a proprietária.  
O objetivo central é preencher a lacuna existente na gestão da empresa, que atualmente não dispõe de nenhuma ferramenta de gerenciamento automatizada. Assim, foi projetado e teve seu desenvolvimento iniciado em Extensão Curricular 1, um sistema que integrará PDV, controle de estoque e gestão financeira.  
O cenário organizacional da Linda Gestante reflete a realidade de muitas microempresas brasileiras, nas quais a gestão é centralizada na figura do proprietário, onde, neste caso, a própria é responsável pelas atividades administrativas, financeiras, de marketing e vendas.  
Na empresa em questão, as vendas são feitas majoritariamente por meio de redes sociais como WhatsApp e Instagram, que também funcionam como vitrine digital da loja, o controle financeiro é realizado por meio de anotações manuais do fluxo de caixa e o gerenciamento do estoque é feito de forma totalmente informal, confiando na memória da gestora e em verificações manuais dos produtos disponíveis.  
Esse modelo de gestão, ainda que comum, acarreta riscos relevantes, como perda de informações, dificuldade na reposição de mercadorias, baixa previsibilidade de demanda, além de contribuir para sobrecarga de trabalho, estresse e tomada de decisões com base em dados imprecisos. A ausência de um sistema informatizado limita o potencial de crescimento da empresa e dificulta a consolidação de estratégias mais eficientes de comercialização e gestão.  
A proposta deste projeto, portanto, foi desenvolver um sistema web que atenda às necessidades específicas da loja, oferecendo funcionalidades de controle de estoque, registro de vendas, emissão de relatórios e cadastro de produtos. Com a posterior implementação do sistema Gesthar, espera-se que a empresa tenha  uma grande melhoria na organização e rastreabilidade do seu estoque, otimizando os processos de gestão e fornecendo informações confiáveis para a tomada de decisões. 

# **2 JUSTIFICATIVA** {#2-justificativa}

Como pré-requisito para a graduação no curso Tecnólogo em Análise e Desenvolvimento de Sistemas (TADS) do IFPI, os alunos participam de atividades extensionistas. Essas atividades visam aplicar os conhecimentos adquiridos em sala de aula para atender a demandas reais da comunidade, promovendo uma troca valiosa entre a academia e a comunidade externa. Nesse contexto, desenvolvemos módulos do sistema PDV e controle de estoque para a empresa Linda Gestante, uma loja de confecções para gestantes localizada em Parnaíba, Piauí. Este projeto está sendo desenvolvido gratuitamente pelos alunos, cabendo à empresa parceira os custos relacionados à infraestrutura tecnológica, necessária para a implementação.  
Esse projeto se torna relevante quando levantam-se dois pontos: primeiramente, ele proporciona aos alunos do curso de ADS uma experiência prática, permitindo-lhes aplicar os conceitos e metodologias aprendidos em um cenário real, de maneira integrada, algo que dificilmente aconteceria na academia. Essa vivência é de suma importância para o desenvolvimento de habilidades técnicas e de resolução de problemas, fortalecendo a formação profissional, o trabalho em equipe e a capacidade de transformar uma necessidade em uma solução funcional.  
Em segundo lugar, o projeto se justifica pela demanda da empresa parceira, que enfrenta desafios relacionados à gestão manual de vendas e controle de estoque. A ausência de um sistema informatizado compromete a agilidade e a confiabilidade dos dados operacionais, dificultando a tomada de decisões estratégicas e o crescimento do negócio. Nesse sentido, a implementação de um sistema PDV com funcionalidades integradas de controle de estoque representa um avanço considerável na profissionalização da gestão da loja parceira.

# **3 OBJETIVOS**  {#3-objetivos}

## 3.1 OBJETIVO GERAL 

	  
Desenvolver um Sistema de Controle de Estoque e Ponto de Venda para atender às necessidades da loja Linda Gestante no controle e gestão de estoque e vendas.

## 3.2 OBJETIVOS ESPECÍFICOS 

O Sistema Linda Gestante foi projetado para ser capaz de registrar e automatizar o processo das vendas, atualizando automaticamente as quantidades em estoque, de forma a gerar relatórios úteis para a realização de pedidos de reposições, promoções e liquidações. Com a implementação do sistema, espera-se:

1. Automatizar o controle de estoque da loja;  
2. Vincular o sistema a plataforma de Nota Fiscal Eletrônica para automatizar os lançamentos para o fisco;  
3. Elaborar uma funcionalidade para controle de preço de revenda das peças podendo ser ajustado facilmente através do sistema;  
4. Atrelar o sistema de recebimentos via Pix, Cartões de Crédito ou Débito e Dinheiro,  para o cliente escolher a melhor forma de pagamento;  
5. Criar alertas de estoque, quando atingir quantidade mínima configurável de produtos com alta saída;

## 3.3 DIFERENCIAIS DO SISTEMA GESTHAR {#3.3-diferenciais-do-sistema-gesthar}

O sistema Gesthar se diferencia de soluções genéricas de PDV por combinar especialização de domínio com arquitetura tecnológica moderna, atendendo especificamente às necessidades de microempresas do segmento de moda gestante:

### 3.3.1 ESPECIALIZAÇÃO PARA O NICHO DE MODA GESTANTE {#3.3.1-especialização-para-o-nicho-de-moda-gestante}

O sistema incorpora funcionalidades específicas para o público-alvo da Linda Gestante, como o campo "Data Prevista do Parto" no cadastro de clientes, que possibilita ações de marketing direcionadas e antecipação de necessidades sazonais. Além disso, oferece controle detalhado de variações (tamanhos específicos para gestantes, cores e modelos) com gestão independente por SKU, e mantém histórico de preferências e compras permitindo atendimento personalizado e sugestões baseadas em comportamento de compra.

### 3.3.2 ARQUITETURA PARA MICROEMPRESAS {#3.3.2-arquitetura-para-microempresas}

A escolha de uma stack open-source (Django \+ PostgreSQL \+ Bootstrap) elimina mensalidades de sistemas SaaS e custos de licenciamento, mantendo o investimento limitado apenas à infraestrutura (VPS). A interface intuitiva foi validada através de 19 protótipos aprovados pela cliente antes da implementação, garantindo usabilidade sem necessidade de treinamento extensivo. A escalabilidade modular permite que funcionalidades sejam implementadas progressivamente conforme demanda real, evitando complexidade desnecessária.

### 3.3.3 AUTONOMIA OPERACIONAL E INTELIGÊNCIA DE NEGÓCIO {#3.3.3-autonomia-operacional-e-inteligência-de-negócio}

O Gesthar promove autonomia administrativa através de alertas automatizados de estoque mínimo baseados em histórico de vendas, eliminando rupturas por esquecimento, e sugestões de reposição calculadas automaticamente considerando sazonalidade e giro de produtos. A descentralização do conhecimento é alcançada pelo registro sistemático de estoque, histórico de clientes e operações no sistema, reduzindo a dependência da memória da proprietária. Os relatórios gerenciais transformam dados operacionais em insights acionáveis, como produtos mais vendidos, margem de lucro e formas de pagamento preferidas.

### 3.3.4 INTEGRAÇÃO E SEGURANÇA {#3.3.4-integração-e-segurança}

A preparação para o ecossistema digital é garantida por uma estrutura API-ready que viabiliza futuras integrações com WhatsApp Business, Instagram Shopping e gateways de pagamento. O sistema mantém auditoria completa com log de todas as operações críticas (vendas, ajustes de estoque, cancelamentos) com rastreabilidade por usuário e timestamp. O controle granular de permissões estabelece distinção entre perfis Administrador e Vendedor com restrições por módulo, enquanto a arquitetura está preparada para conformidade fiscal através da integração com emissores de Nota Fiscal Eletrônica.

### 3.3.5 TECNOLOGIA ACESSÍVEL E SUSTENTÁVEL {#3.3.5-tecnologia-acessível-e-sustentável}

A arquitetura MTV (Model-Template-View) do Django proporciona separação clara de responsabilidades, facilitando a manutenção e evolução futura do sistema. A responsividade nativa permite funcionamento em desktop, tablet e smartphone sem instalação de aplicativos, apenas via navegador. O ORM nativo oferece abstração do banco de dados permitindo migração entre SGBDs sem reescrita de código, enquanto a performance otimizada através de queries indexadas garante tempo de resposta inferior a 3 segundos para operações normais.

Esses diferenciais posicionam o Gesthar como uma solução estratégica de gestão que compreende tanto as particularidades do segmento de moda para gestantes quanto às limitações operacionais de microempreendimentos, oferecendo profissionalização tecnológica acessível sem comprometer a flexibilidade necessária para negócios de pequeno porte.

# **4 REFERENCIAL TEÓRICO** {#4-referencial-teórico}

O uso de softwares de gerenciamento é essencial hoje, devido ao avanço tecnológico nas transações bancárias e fiscais. Mesmo pequenos empreendimentos têm adquirido seus próprios sistemas, mas o custo de manutenção dos mesmos tende a não ser compatível com o tamanho desses negócios. Prover então um sistema que organize e melhore a eficiência da Linda Gestante é o principal objetivo desse projeto.

O uso da tecnologia da informação aplicada à automação comercial vem transformando significativamente os processos organizacionais, permitindo não apenas o registro e controle de operações, mas também a geração de relatórios analíticos que subsidiam a tomada de decisão estratégica (LIMA et al., 2023).

Segundo Sato (2016), a adoção de sistemas informatizados no controle de estoques promove melhorias substanciais na organização dos produtos, evitando perdas, identificando rapidamente os itens mais vendidos e otimizando o processo de reposição. Em sua pesquisa, o autor destaca a importância da aplicação do ciclo PDCA (Plan-Do-Check-Act) como ferramenta de gestão contínua, especialmente no contexto de comércios de roupas, onde a rotatividade de produtos é alta e as tendências de consumo são sazonais.

Além disso, o controle de estoque informatizado contribui para a padronização de processos e a confiabilidade dos dados operacionais. Segundo Carvalho (2015), sistemas desenvolvidos para pequenos comércios permitem uma integração entre vendas e estoque, facilitando o acompanhamento das movimentações em tempo real e promovendo agilidade nas operações. Ele destaca que a disponibilização de módulos garante aos gestores maior controle e previsibilidade sobre o negócio.

Carranza (2018) reforça que o planejamento e o controle são funções administrativas essenciais para o sucesso organizacional. A autora destaca que, no contexto de micro e pequenas empresas, a adoção de tecnologias gerenciais possibilita uma gestão mais eficiente, promovendo maior competitividade e sustentabilidade no mercado.

Outro aspecto relevante é a integração entre os sistemas de vendas (PDV) e os meios de pagamento. Sistemas modernos permitem a vinculação com métodos diversos, como Pix, cartões e dinheiro, o que aumenta a conveniência para o cliente e fortalece a experiência de compra. Como apontado por Lima *et a*l. (2023), essa funcionalidade também permite ao gestor identificar quais formas de pagamento são mais utilizadas e tomar decisões que melhorem os fluxos de caixa.

# **5 RESULTADOS ALCANÇADOS (EXTENSÃO CURRICULAR I)** {#5-resultados-alcançados-(extensão-curricular-i)}

Durante a execução da disciplina Extensão Curricular I, no período de setembro de 2025 a janeiro de 2026, a equipe concluiu as etapas de planejamento, análise e o desenvolvimento dos módulos estruturais do sistema Gesthar. Os seguintes resultados foram alcançados:

## 5.1 ANÁLISE E PLANEJAMENTO {#5.1-análise-e-planejamento}

Foi realizado o levantamento completo dos problemas e requisitos funcionais e não funcionais do sistema. Com base nesta análise, foram elaborados os Diagramas de Caso de Uso , Diagrama de Classe e o Diagrama de Entidade e Relacionamento.

## 5.2 PROTOTIPAÇÃO DE TELAS {#5.2-prototipação-de-telas}

Durante esta etapa, a equipe utilizou a ferramenta Figma para criar protótipos de alta fidelidade. Esta atividade foi essencial para validar as regras de negócio e o fluxo de navegação junto à cliente. Os protótipos aprovados resultantes desta etapa foram incorporados à documentação técnica do sistema.

## 5.3 CONFIGURAÇÃO DO AMBIENTE {#5.3-configuração-do-ambiente}

O ambiente de desenvolvimento foi configurado, utilizando o framework Django, o banco de dados PostgreSQL e o framework front-end Bootstrap. O controle de versão foi gerenciado através de Git e Github.

## 5.4 MÓDULO DE PRODUTOS E CONTROLE DE ESTOQUE {#5.4-módulo-de-produtos-e-controle-de-estoque}

Foi desenvolvido o módulo completo de Cadastro de Produtos e Controle de Estoque. A funcionalidade permite o registro de produtos com todos os atributos definidos (tamanho, cor, SKU, estoque mínimo, etc.) e realiza o controle de entrada e saída de mercadorias.

## 5.5 MÓDULO DE PONTO DE VENDA (PDV) {#5.5-módulo-de-ponto-de-venda-(pdv)}

A funcionalidade central do Ponto de Venda (PDV) foi implementada. A interface permite buscar produtos, adicionar itens ao carrinho, aplicar descontos e finalizar a venda. A baixa no estoque é realizada automaticamente. Nesta primeira etapa, a integração com gateways de pagamento (PIX e Cartão de Crédito) ainda não foi implementada no sistema.

## 5.6 MÓDULOS DE USUÁRIOS E CLIENTES {#5.6-módulos-de-usuários-e-clientes}

Foi desenvolvido o sistema de Login e autenticação de usuários. O controle de acesso detalhado por permissões (Administrador/Vendedor) não foi implementado nesta fase. 

# **6 METODOLOGIA DA EXECUÇÃO DO PROJETO** {#6-metodologia-da-execução-do-projeto}

	Como metodologia para o desenvolvimento do software de gestão, a equipe escolheu aplicar métodos ágeis. Segundo Soares (2004), as metodologias ágeis surgiram com a proposta de aumentar o enfoque nas pessoas e não nos processos de desenvolvimento. Para organizar esse trabalho, decidiu-se por aplicar quadro *Kanban* através do Jira e realizar sprints iterativos para a entrega das metas estabelecidas.  
	Valente (2020) define um quadro *Kanban* como um quadro de tarefas que também inclui o Backlog do Produto. No quadro desenvolvido para o projeto, definiram-se as tarefas a serem realizadas nas sprints da primeira etapa, que tratou do levantamento de requisitos, criação de diagramas UML e prototipação de telas, além da presente documentação e módulos do sistema desenvolvidos. Cada membro da equipe então assumiu uma ou mais tarefas, a fim de entregar ao final da sprint a primeira etapa do projeto.  
	Ao fim de cada sprint era realizado um novo alinhamento para definição de tarefas, a partir da documentação inicial e das metas a serem atingidas. 

# 

# **7 ESPECIFICAÇÃO DO SISTEMA** {#7-especificação-do-sistema}

## 7.1 LISTA DE REQUISITOS FUNCIONAIS {#7.1-lista-de-requisitos-funcionais}

### 7.1.1 CONTROLE DE ESTOQUE {#7.1.1-controle-de-estoque}

Tabela 1 \- Requisitos Funcionais (RF) de Controle de Estoque

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RF001 | Cadastrar produtos | O sistema deverá permitir o cadastro de produtos com os seguintes campos: \- Nome do produto \- Descrição \- Categoria (blusas, calças, etc.) \- Tamanhos disponíveis (PP, P, M, etc.) \- Cores disponíveis \- Preço de custo \- Preço de venda \- Margem de lucro (calculada) \- Fornecedor \- Código interno/SKU \- Estoque mínimo |
| RF002 | Controlar entrada de mercadorias | O sistema deverá gerenciar a entrada de mercadorias: \- Registro de compras/recebimentos \- Atualização automática do estoque |
| RF003 | Controlar saída de mercadorias | O sistema deverá gerenciar a saída de mercadorias: \- Baixa automática no estoque após venda \- Controle de perdas/avarias \- Transferências entre lojas (quando aplicável) |
| RF004 | Emitir alertas de estoque | O sistema deverá notificar sobre o nível do estoque: \- Notificação quando produto atingir estoque mínimo \- Lista de produtos em falta \- Sugestão de reposição baseada no histórico de vendas |
| RF005 | Realizar inventário | O sistema deverá fornecer ferramentas para o inventário: \- Função para contagem de estoque \- Ajustes de estoque com justificativa \- Relatório de divergências |

Fonte: Autoria Própria (2025)

### 7.1.2 CADASTRO DE USUÁRIOS (FUNCIONÁRIOS) {#7.1.2-cadastro-de-usuários-(funcionários)}

Tabela 2 \- Requisitos Funcionais (RF) de Cadastro de Usuários

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RF006 | Cadastrar usuários do sistema | O sistema deverá permitir o cadastro de usuários (funcionários) com os campos: \- Nome completo \- CPF \- Email \- Telefone \- Cargo/função \- Data de admissão \- Status (ativo/inativo) |
| RF007 | Controlar acesso de usuários | O sistema deverá gerenciar o acesso dos usuários: \- Login e senha \- Perfis de acesso (Administrador, Vendedor) \- Permissões específicas por módulo \- Log de atividades dos usuários |
| RF008 | Recuperar senha | O sistema deverá permitir a recuperação de senha via email. |

Fonte: Autoria Própria (2025)

### 7.1.3 CADASTRO DE CLIENTES {#7.1.3-cadastro-de-clientes}

Tabela 3 \- Requisitos Funcionais (RF) de Cadastro de Clientes

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RF009 | Cadastrar clientes | O sistema deverá permitir o cadastro de clientes com os seguintes dados: \- Nome completo \- CPF/CNPJ \- Data de nascimento \- Telefone/WhatsApp \- Email \- Endereço completo \- Data prevista do parto (específico) \- Preferências de tamanho \- Observações |
| RF010 | Manter histórico do cliente | O sistema deverá armazenar o histórico do cliente: \- Todas as compras realizadas \- Valor total gasto \- Frequência de compras \- Produtos preferidos |
| RF011 | Comunicar-se com cliente (Opcional) | O sistema poderá, opcionalmente, facilitar a comunicação: \- Envio de ofertas por email/SMS \- Lembretes de aniversário \- Notificações de chegada de produtos |

Fonte: Autoria Própria (2025)

### 7.1.4 PONTO DE VENDA (PDV) {#7.1.4-ponto-de-venda-(pdv)}

Tabela 4 \- Requisitos Funcionais (RF) de Ponto de Venda

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RF012 | Operar interface de venda | A interface de venda deverá permitir: \- Busca de produtos por nome, código SKU \- Adição/remoção de itens no carrinho \- Aplicação de descontos ou acréscimos \- Cálculo automático de total e troco |
| RF013 | Finalizar venda | O sistema deverá processar a finalização da venda: \- Seleção de cliente (obrigatório ou opcional) \- Formas de pagamento: dinheiro, cartão, PIX \- Parcelamento (se aplicável) \- Emissão de cupom fiscal/recibo \- Impressão de comprovante |
| RF014 | Realizar gestão de vendas | O sistema deverá permitir o gerenciamento das vendas: \- Cancelamento de vendas (com justificativa) \- Troca de produtos \- Devolução de produtos \- Sangria e suprimento de caixa |
| RF015 | Realizar fechamento de caixa | O sistema deverá auxiliar no fechamento do caixa: \- Relatório de vendas do dia \- Conferência de valores por forma de pagamento \- Registro de sangrias e suprimentos |

Fonte: Autoria Própria (2025)

### 7.1.5 RELATÓRIOS {#7.1.5-relatórios}

Tabela 5 \- Requisitos Funcionais (RF) de Relatórios

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RF016 | Gerar relatórios de estoque | O sistema deverá emitir relatórios de estoque: \- Posição atual de estoque \- Produtos com estoque baixo \- Produtos mais vendidos \- Produtos parados (sem movimento) \- Valor total do estoque \- Relatório de entrada e saída por período |
| RF017 | Gerar relatórios de vendas | O sistema deverá emitir relatórios de vendas: \- Vendas por período (dia, semana, mês, ano) \- Vendas por produto \- Vendas por vendedor \- Vendas por cliente \- Formas de pagamento utilizadas \- Meta vs. realizado |
| RF018 | Gerar relatórios financeiros | O sistema deverá emitir relatórios financeiros: \- Faturamento por período \- Margem de lucro por produto \- Comissões de vendedores \- Fluxo de caixa |

Fonte: Autoria Própria (2025)

## 7.2 LISTA DE REQUISITOS NÃO FUNCIONAIS {#7.2-lista-de-requisitos-não-funcionais}

### 7.2.1 USABILIDADE {#7.2.1-usabilidade}

Tabela 6 \- Requisitos Não Funcionais (RNF) de Usabilidade

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF001 | Facilidade de uso e Desempenho | \- Interface intuitiva e de fácil navegação. \- Sistema responsivo (compatível com tablets e smartphones). \- Tempo de resposta inferior a 3 segundos para operações normais. |

Fonte: Autoria Própria (2025)

### 7.2.2 SEGURANÇA {#7.2.2-segurança}

Tabela 7 \- Requisitos Não Funcionais (RNF) de Segurança

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF002 | Segurança dos dados | \- Backup automático ou manual. \- Acesso apenas via HTTPS. |

Fonte: Autoria Própria (2025)

### 7.2.3 COMPATIBILIDADE {#7.2.3-compatibilidade}

Tabela 8 \- Requisitos Não Funcionais (RNF) de Compatibilidade

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF003 | Compatibilidade | \- Compatível com principais navegadores (Chrome, Firefox, Edge, etc). \- Suporte a impressoras térmicas para cupons. \- Integração com leitores de código de barras. |

Fonte: Autoria Própria (2025)

### 7.2.4 DISPONIBILIDADE {#7.2.4-disponibilidade}

Tabela 9 \- Requisitos Não Funcionais (RNF) de Disponibilidade

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF004 | Disponibilidade | \- Sistema disponível 99% do tempo. \- Funcionalidade offline básica para vendas (sincronização posterior). |

Fonte: Autoria Própria (2025)

### 7.2.5  EQUIPAMENTOS {#7.2.5-equipamentos}

Tabela 10 \- Requisitos Não Funcionais (RNF) de Equipamentos

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF005 | Integração com Equipamentos | \- Integração com Impressora fiscal/não fiscal. \- Integração com Leitor de código de barras. |

Fonte: Autoria Própria (2025)

### 7.2.6 SERVIÇOS EXTERNOS {#7.2.6-serviços-externos}

Tabela 11 \- Requisitos Não Funcionais (RNF) de Serviços Externos

| Índice | Requisito | Descrição |
| :---- | :---- | :---- |
| RNF006 | Integração com Serviços Externos | \- Consulta de CEP (ViaCEP ou similar). \- Gateway de pagamento PIX. |

Fonte: Autoria Própria (2025)

## 

## 7.3 MODELAGEM E ARQUITETURA DO SISTEMA {#7.3-modelagem-e-arquitetura-do-sistema}

Para fundamentar o desenvolvimento do projeto Gesthar e garantir a integridade da arquitetura de software, foram elaborados artefatos visuais baseados na linguagem UML (Unified Modeling Language) e em conceitos de modelagem de dados. Esta etapa foi essencial para documentar os requisitos funcionais, a estrutura lógica das classes e o esquema de persistência das informações.

O detalhamento técnico completo, contendo o Diagrama de Casos de Uso (interações do usuário), o Diagrama de Classes (estrutura do backend) e o Diagrama de Entidade e Relacionamento (banco de dados), encontra-se disponível para consulta no Apêndice A – Documentação Técnica e Diagramas do Sistema.

## 

## 7.4 PROTOTIPAÇÃO DE TELAS {#7.4-prototipação-de-telas}

Para a definição da interface visual, foram desenvolvidos protótipos navegáveis que representam a versão final do front-end do sistema. O detalhamento completo das telas, incluindo fluxos de Login, Vendas e Relatórios, encontra-se disponível para consulta no Apêndice B.  
As telas finais do sistema, resultantes da implementação dos módulos descritos, podem ser visualizadas na íntegra no Apêndice C deste documento.

## 

## 7.5 TECNOLOGIAS UTILIZADAS {#7.5-tecnologias-utilizadas}

Para o desenvolvimento do projeto, foram escolhidas tecnologias consolidadas no mercado, levando em consideração pontos importantes como robustez, produtividade e facilidade de manutenção. 

### 7.5.1 FIGMA {#7.5.1-figma}

O Figma é uma plataforma colaborativa baseada na nuvem que permite o desenvolvimento de layouts interativos e a validação visual das telas antes da implementação. Foi escolhido como ferramenta de design de interface para a criação dos protótipos de alta fidelidade do sistema, pois sua interface intuitiva, aliada à possibilidade de trabalho em equipe em tempo real, contribui para um fluxo de design mais ágil e alinhado com os princípios de interface e experiência do usuário.

###  7.5.2 POSTGRESQL {#7.5.2-postgresql}

Foi escolhido como sistema gerenciador de banco de dados relacional por ser uma solução open-source consolidada, segura e com alto desempenho. Ele oferece suporte avançado a integridade referencial, transações e extensibilidade, o que o torna ideal para aplicações que exigem confiabilidade e estruturação eficiente dos dados utilizados.

### 7.5.3 DJANGO {#7.5.3-django}

É um framework desenvolvido em python escolhido para construção do backend da solução. Ele oferece uma arquitetura robusta baseada no padrão MTV(Model-Template-View), além de ferramentas integradas que aceleram o desenvolvimento, como ORM(Object relational mapping), sistema de autenticação, painel administrativo e roteamento automático. O Django também favorece boas práticas de segurança e organização de código.

### 7.5.4 BOOTSTRAP {#7.5.4-bootstrap}

Para o desenvolvimento do frontend da solução, optamos por utilizar um framework CSS que facilita a criação de interfaces responsivas e modernas, o Bootstrap. Com seus componentes pré-prontos e sistema de grid, ele acelera o desenvolvimento e garante uma experiência visual confortável em diferentes dispositivos, sem a necessidade de criar estilos do zero.

#  **8 RESULTADOS ESPERADOS** {#8-resultados-esperados}

A execução do presente projeto tem como finalidade proporcionar melhorias significativas na gestão da loja Linda Gestante, a partir da implementação de um sistema informatizado de Ponto de Venda (PDV) com controle de estoque. Espera-se, com isso, alcançar os seguintes resultados:

1. Aprimoramento da gestão organizacional, por meio da automatização de processos relacionados às vendas, ao controle de estoque e à geração de relatórios gerenciais;  
2. Redução de falhas operacionais, decorrentes de anotações manuais e da ausência de um sistema estruturado, promovendo maior confiabilidade e rastreabilidade das informações;  
3. Descentralização das atividades administrativas, possibilitando que a operação da loja não dependa exclusivamente da figura da proprietária;  
4. Melhoria na tomada de decisões estratégicas, com base em dados atualizados e indicadores extraídos de relatórios personalizados;  
5. Incremento no controle financeiro e fiscal, com suporte à emissão de comprovantes e integração com múltiplas formas de pagamento, como Pix e cartões;  
6. Aumento na qualidade do atendimento ao cliente, por meio de processos de venda mais automatizados,ágeis e eficientes.

## 

# **9 DISSEMINAÇÃO DOS RESULTADOS** {#9-disseminação-dos-resultados}

A disseminação dos resultados do projeto será realizada em etapas, alinhadas às entregas das disciplinas de Extensão Curricular I e Extensão Curricular II, sendo elas:

1. Apresentação institucional do projeto em eventos acadêmicos promovidos pelo Instituto Federal do Piauí, como IFPI no Shopping;  
2. Elaboração deste documento, que formaliza a análise, o planejamento (requisitos, diagramas, protótipos) e o desenvolvimento inicial do sistema, servindo como a entrega formal para a empresa parceira da primeira fase do projeto;  
3. Apresentação, à banca avaliadora do curso, dos resultados obtidos, validando as metodologias aplicadas e o progresso do desenvolvimento.

Espera-se, portanto, que o projeto contribua tanto para os processos da empresa parceira quanto para o desenvolvimento das competências profissionais e sociais dos discentes envolvidos, reafirmando o papel da extensão universitária como elo entre a academia e a comunidade.

# **10 CRONOGRAMA DE EXECUÇÃO** {#10-cronograma-de-execução}

Tabela 12 \- Cronograma de Atividades Executadas

| ATIVIDADE | 2025 |  |  |  |  |  |  | 2026 |  |  |  |  |  |  |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
|  | J | J | A | S | O | N | D | J | F | M | A | M | J | J |
| **Levantamento do Problema do Cliente** | x |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **Levantamento dos Requisitos** |  | x |  |  |  |  |  |  |  |  |  |  |  |  |
| **Criação dos Diagramas** |  | x |  |  |  |  |  |  |  |  |  |  |  |  |
| **Criação dos Protótipos Navegáveis de Todas as Telas do Sistema** |  |  | x |  |  |  |  |  |  |  |  |  |  |  |
| **Configurar Ambiente de Desenvolvimento** |  |  |  | x |  |  |  |  |  |  |  |  |  |  |
| **Módulo de Cadastro de Produtos e Controle de Estoque** |  |  |  | x | x |  |  |  |  |  |  |  |  |  |
| **Ponto de Venda** |  |  |  |  |  | x | x | x |  |  |  |  |  |  |
| **Sistema de Login e Controle de Acesso** |  |  |  |  |  |  | x | x |  |  |  |  |  |  |
| **Cadastro de Clientes** |  |  |  |  |  |  | x | x |  |  |  |  |  |  |
| **Gateways de Pagamento** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **Deploy e Testagem em Ambiente de Desenvolvimento** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **Dashboard e Relatórios Financeiros** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **Implantação na Loja**  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| **Entregar o sistema funcional completo e defesa para banca final** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

# 

# **11 CONSIDERAÇÕES FINAIS** {#11-considerações-finais}

Este projeto documentou o trabalho de análise, planejamento e desenvolvimento de software realizado durante a disciplina de Extensão Curricular I, aplicado às necessidades da empresa Linda Gestante. Os objetivos propostos para esta primeira fase foram alcançados, resultando em uma base sólida para a digitalização da gestão da loja.

O trabalho concluído nesta etapa entregou não apenas o planejamento completo do sistema — incluindo o levantamento de requisitos, a criação de diagramas UML e de entidade-relacionamento, e a prototipação de todas as telas — mas também o desenvolvimento dos módulos centrais da aplicação. O sistema Gesthar encontra-se funcional, com os módulos de Login, Cadastro de Produtos e Controle de Estoque implementados, além de um Ponto de Venda (PDV) operacional para o registro de vendas e baixa automática de estoque.

A metodologia ágil, gerenciada através do quadro Kanban e sprints iterativos, provou ser eficaz para a organização da equipe e para garantir entregas incrementais de valor.

O projeto terá sua continuidade na disciplina de Extensão Curricular II, onde a equipe se concentrará na finalização do módulo de Clientes, na implementação do controle de acesso detalhado por permissões, na integração dos gateways de pagamento (PIX e Cartão) ao PDV e no desenvolvimento completo dos módulos de Dashboard e Relatórios Financeiros.

Conclui-se que este projeto reafirma o papel da extensão universitária como elo fundamental entre a academia e a comunidade. Além de proporcionar uma melhoria tangível e profissionalizante para a gestão da empresa parceira, o projeto ofereceu aos discentes uma valiosa experiência prática, permitindo a aplicação direta dos conhecimentos de Análise e Desenvolvimento de Sistemas em um problema real de mercado.

# **12 REFERÊNCIAS** {#12-referências}

LIMA, Bruno Danny; NASCIMENTO, Vinícius Alexander Moreira; NETO, Geraldo Henrique. **Desenvolvimento de um protótipo para controle de vendas de uma loja atuante no segmento de comércio de roupas.** Uni-FACEF, \[s.d.\].

CARRANZA, Giovanna. **Administração geral e pública: para os concursos de analista e técnico.** 3\. ed. Salvador: Juspodivm, 2018\.

CARVALHO, Eduardo Costa. **Sistema de gerenciamento de estoque e vendas para loja de materiais de construção**. Assis: Instituto Municipal de Ensino Superior de Assis, 2015\. Trabalho de Conclusão de Curso (Graduação em Análise e Desenvolvimento de Sistemas).

SATO, Leandro Kenji Inagaki. **Proposta de implantação de um sistema de gestão de estoque em um comércio de roupas: um estudo de caso**. Universidade Federal da Grande Dourados, 2016\. Trabalho de Conclusão de Curso.

SOARES, Michel dos Santos. **Comparação entre Metodologias Ágeis e Tradicionais para o Desenvolvimento de Software.** INFOCOMP Journal of Computer Science**,** *\[S. l.\]*, v. 3, n. 2, p. 8–13, 2004\. Disponível em: https://infocomp.dcc.ufla.br/index.php/infocomp/article/view/68. Acesso em: 11 jul. 2025\.

VALENTE, Marco Tulio. **Engenharia de Software Moderna: Princípios e Práticas para Desenvolvimento de Software com Produtividade**. Editora Independente, 2020\.

# 

# 

# **APÊNDICE A \- DOCUMENTAÇÃO TÉCNICA E DIAGRAMAS DE SISTEMAS** {#apêndice-a---documentação-técnica-e-diagramas-de-sistemas}

Figura A.1 – Diagrama de Casos de Uso![][image2]  
Fonte: Autoria Própria (2025)

Figura A.2 \- Diagrama de Classe  
**![][image3]**  
Fonte: Autoria Própria (2025)

Figura A.3 \- Diagrama de Entidade e Relacionamento  
![][image4]

##  

Fonte: Autoria Própria (2025)

# 

# 

# 

# 

# 

# 

# **APÊNDICE B \- PROTOTIPAÇÃO DE TELAS** {#apêndice-b---prototipação-de-telas}

Figura B.1 \- Protótipo do Login  
![][image5]  
Fonte: Autoria Própria (2025)

### 

Figura B.2 \- Protótipo do Ponto de Venda  
![][image6]  
Fonte: Autoria Própria (2025)  
Figura B.3 \- Protótipo do Pagamento da Venda  
![][image7]  
Fonte: Autoria Própria (2025)

### 

Figura B.4 \- Protótipo da Confirmação de Recibo  
![][image8]  
Fonte: Autoria Própria (2025)

Figura B.5 \- Protótipo da Consulta de Vendas  
![][image9]  
Fonte: Autoria Própria (2025)

### 

Figura B.6 \- Protótipo da Visualização da Venda  
![][image10]  
Fonte: Autoria Própria (2025)  
Figura B.7 \- Protótipo do Cadastro do Produto  
![][image11]  
Fonte: Autoria Própria (2025)

### 

Figura B.8 \- Protótipo da Visualização do Produto  
![][image12]  
Fonte: Autoria Própria (2025)

Figura B.9 \- Protótipo da Visualização Completa do Produto  
![][image13]  
Fonte: Autoria Própria (2025)

### 

Figura B.10 \- Protótipo do Cadastro do Cliente  
![][image14]  
Fonte: Autoria Própria (2025)

### 

Figura B.11 \- Protótipo da Visualização dos Clientes  
![][image15]  
Fonte: Autoria Própria (2025)

### 

Figura B.12 \- Protótipo da Visualização Completa do Cliente  
	![][image16]  
Fonte: Autoria Própria (2025)

### 

Figura B.13 \- Protótipo do Relatório de Estoque  
![][image17]  
Fonte: Autoria Própria (2025)

### 

Figura B.14 \- Protótipo do Relatório Financeiro  
![][image18]  
Fonte: Autoria Própria (2025)

### 

Figura B.15 \- Protótipo do Relatório de Vendas  
![][image19]  
Fonte: Autoria Própria (2025)

### 

Figura B.16 \- Protótipo do Relatório de Divergências  
![][image20]  
Fonte: Autoria Própria (2025)

Figura B.17 \- Protótipo do Cadastro de Usuários  
![][image21]  
Fonte: Autoria Própria (2025)

### 

Figura B.18- Protótipo da Visualização dos Usuários  
![][image22]  
Fonte: Autoria Própria (2025)

### 

Figura B.19 \- Protótipo da Visualização Completa do Usuário  
![][image23]  
Fonte: Autoria Própria (2025)

# **APÊNDICE C \- TELAS DO SISTEMA IMPLEMENTADO** {#apêndice-c---telas-do-sistema-implementado}

Figura C.1 \- Tela de Login  
![][image24]  
Fonte: Autoria Própria (2025)

Figura C.2 \- Tela Inicial (Homepage)  
![][image25]  
Fonte: Autoria Própria (2025)

Figura C.3 \- Tela de Ponto de Venda (PDV)  
![][image26]  
Fonte: Autoria Própria (2025)

Figura C.4 \- Tela de Cadastro de Produto  
![][image27]  
Fonte: Autoria Própria (2025)

Figura C.5 \- Tela de Lista de Produtos  
![][image28]  
Fonte: Autoria Própria (2025)

Figura C.6 \- Tela de Detalhes do Produtos  
![][image29]  
Fonte: Autoria Própria (2025)

Figura C.7 \- Tela de Cadastro do Cliente 1  
![][image30]  
Fonte: Autoria Própria (2025)

Figura C.8 \- Tela de Cadastro do Cliente 2  
![][image31]  
Fonte: Autoria Própria (2025)

Figura C.9 \- Tela de Lista de Clientes  
![][image32]  
Fonte: Autoria Própria (2025)

Figura C.10 \- Tela de Detalhes do Cliente  
![][image33]  
Fonte: Autoria Própria (2025)

Figura C.11 \- Tela de Lista de Usuários  
![][image34]  
Fonte: Autoria Própria (2025)

Figura C.11 \- Tela de Detalhes do Usuário  
![][image35]  
Fonte: Autoria Própria (2025)
