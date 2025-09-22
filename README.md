# Gesthar 🤰
![Static Badge](https://img.shields.io/badge/Status-Desenvolvimento-grey?style=flat&logo=devbox&logoColor=white&labelColor=A52A2A&color=%23FFB6C1)

## 📋 Sumário

- [Padrão de Commits](#padrão-de-commits)

## Padrão de Commits

**`Estrutura da Mensagem de Commit`**

>`!`: indica os atributos obrigatórios

>`?`: indica os atributos opcionais

```
!tipo(?escopo): !descrição

?corpo
```
| Atributo | Detalhe | Observações |
| ----------- | ----------- | ----------- |
| tipo | Uma única palavra em minúsculas que define a categoria da alteração | [Tipos de commits](https://medium.com/linkapi-solutions/conventional-commits-pattern-3778d1a1e657)
| escopo | Identifica parte do código alterada | 1. fix(login): corrige validação de senha (a correção foi na área de login).<br>2. feat(api): adiciona endpoint de usuários (a nova funcionalidade foi na API).
| descrição | Um resumo curto e direto do que a alteração faz | 1. Comece com letra minúscula. <br>2. Use o modo imperativo (como se estivesse dando uma ordem): "corrige", "adiciona", "remove" em vez de "corrigido", "adicionando". <br>3. Não termine com um ponto final.
| corpo | Texto mais longo e detalhado | Use o corpo para fornecer contexto que não cabe na descrição

`Exemplo`
```
docs(readme): documenta o padrão de commits do projeto

Esta alteração adiciona uma seção detalhada ao README para formalizar o padrão de mensagens de commit (Conventional Commits) a ser utilizado no projeto.
```
