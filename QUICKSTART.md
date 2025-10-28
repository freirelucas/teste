# Guia de Início Rápido

## Configuração Rápida (5 minutos)

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Configure sua chave do Overton
```bash
cp .env.example .env
# Edite .env e adicione sua chave:
# OVERTON_API_KEY=sua_chave_aqui
# OPENALEX_EMAIL=seu_email@exemplo.com (opcional)
```

### 3. Execute a aplicação
```bash
python app.py
```

### 4. Acesse no navegador
Abra: http://localhost:5000

## Testando sem a chave do Overton

Você pode testar a aplicação apenas com OpenAlex:
- Deixe a chave do Overton em branco no .env
- Desmarque "Overton" na interface web
- Busque apenas com OpenAlex

## Endpoints da API

### Buscar pesquisas
```bash
curl "http://localhost:5000/api/search?q=agent%20based%20models"
```

### Ver estatísticas
```bash
curl "http://localhost:5000/api/stats"
```

### Health check
```bash
curl "http://localhost:5000/api/health"
```

## Recursos Principais

- ✅ Busca simultânea em OpenAlex e Overton
- ✅ Foco padrão em "agent based models"
- ✅ Filtros por fonte e quantidade de resultados
- ✅ Visualização de Open Access
- ✅ Conceitos-chave e tópicos
- ✅ Impacto em políticas públicas (Overton)
- ✅ Interface responsiva

## Próximos Passos

Leia o [README.md](README.md) completo para:
- Documentação detalhada da API
- Exemplos de código Python
- Resolução de problemas
- Contribuindo para o projeto
