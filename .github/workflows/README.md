# GitHub Actions - Deploy e Testes

Este workflow automatiza testes e deploy da aplicação no Docker Hub.

## 📋 Configuração Necessária

### 1. Secrets no GitHub

Adicione os seguintes secrets no repositório (**Settings > Secrets and variables > Actions**):

- `DOCKER_USERNAME`: Seu nome de usuário do Docker Hub
- `DOCKER_PASSWORD`: Token de acesso do Docker Hub (não use a senha)

**Como gerar o token:**
1. Vá para [Docker Hub Account Settings](https://hub.docker.com/settings/security)
2. Clique em "New Access Token"
3. Crie um token com permissão de read/write
4. Copie e use como `DOCKER_PASSWORD`

### 2. Variáveis de Ambiente

Se precisar de variáveis de ambiente adicionais durante os testes, adicione-as ao workflow nos respectivos steps.

## 🚀 Como Funciona

### Jobs do Workflow

#### 1. **tests** (Sempre executa)
- Configura Python 3.12
- Instala dependências
- Executa migrações do banco de dados
- Roda todos os testes
- Gera relatório de cobertura
- Envia cobertura para Codecov

#### 2. **deploy** (Executa após tests com sucesso)
- Build da imagem Docker
- Push para Docker Hub
- Tags automáticas: branch, semver, SHA

#### 3. **security-scan** (Análise de vulnerabilidades)
- Verifica vulnerabilidades com Trivy
- Envia relatórios para GitHub Security

## 📝 Triggers

O workflow é acionado em:
- Push nas branches `main` e `develop`
- Pull requests nas branches `main` e `develop`

## 🐳 Imagens no Docker Hub

Após o deploy, as imagens estarão disponíveis em:
```
docker pull <seu-usuario>/gesthar-pdv:develop
docker pull <seu-usuario>/gesthar-pdv:main
docker pull <seu-usuario>/gesthar-pdv:<commit-sha>
```

## ✅ Verificar Status

1. Vá para a aba **Actions** do seu repositório
2. Veja o status dos workflows
3. Clique em um workflow para ver detalhes

## 🔍 Troubleshooting

### Testes falhando
- Verifique se o banco de dados PostgreSQL está configurado corretamente
- Veja os logs do job `tests`

### Docker push falhando
- Valide se os secrets estão configurados
- Verifique permissões do token Docker

### Sem migrations
Se tiver migrações não criadas:
```bash
python manage.py makemigrations
git add */migrations/
git commit -m "feat(migrations): add new migrations"
git push
```

## 📊 Cobertura de Testes

Os relatórios de cobertura são enviados automaticamente para Codecov. Você pode adicionar um badge no README:

```markdown
[![codecov](https://codecov.io/gh/<seu-usuario>/gesthar_pdv/branch/main/graph/badge.svg)](https://codecov.io/gh/<seu-usuario>/gesthar_pdv)
```
