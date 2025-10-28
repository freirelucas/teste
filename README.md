# Agent-Based Models Research Hub

Uma aplicação web integrada para pesquisar e explorar pesquisas acadêmicas sobre **Agent-Based Models** (Modelos Baseados em Agentes) utilizando as APIs do **OpenAlex** e **Overton**.

## 🎯 Funcionalidades

- **Busca Integrada**: Pesquise simultaneamente em OpenAlex (base acadêmica aberta) e Overton (documentos de política)
- **Foco em Agent-Based Models**: Interface otimizada para pesquisas sobre modelos baseados em agentes
- **Visualização Rica**: Apresentação detalhada de resultados com:
  - Metadados completos (autores, ano, citações)
  - Status de Open Access
  - Conceitos-chave e tópicos
  - Impacto em políticas públicas (Overton)
- **Estatísticas em Tempo Real**: Visualize o total de trabalhos disponíveis
- **Interface Responsiva**: Design moderno e adaptável a diferentes dispositivos

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.x**
- **Flask**: Framework web minimalista
- **Flask-CORS**: Suporte para Cross-Origin Resource Sharing
- **Requests**: Cliente HTTP para integração com APIs
- **python-dotenv**: Gerenciamento de variáveis de ambiente

### Frontend
- **HTML5/CSS3**: Interface moderna e responsiva
- **JavaScript (Vanilla)**: Interatividade sem dependências
- **CSS Grid/Flexbox**: Layout responsivo

### APIs Integradas
- **OpenAlex API**: Acesso a milhões de trabalhos acadêmicos open access
- **Overton API**: Documentos de pesquisa mencionados em políticas públicas

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Chave de API do Overton (opcional, mas recomendado)
- Email para OpenAlex (opcional, mas recomendado para melhores rate limits)

## 🚀 Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd teste
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e adicione suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
# Chave de API do Overton (obrigatória para usar o Overton)
OVERTON_API_KEY=sua_chave_aqui

# Email para OpenAlex (opcional, mas recomendado)
OPENALEX_EMAIL=seu_email@exemplo.com
```

### 5. Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 📖 Como Usar

### Interface Web

1. Acesse `http://localhost:5000` no seu navegador
2. A busca padrão já está configurada para "agent based models"
3. Você pode:
   - Modificar o termo de busca
   - Selecionar quais fontes usar (OpenAlex, Overton ou ambas)
   - Ajustar o número de resultados por fonte
4. Clique em "Search" ou pressione Enter

### API Endpoints

#### Buscar Trabalhos
```
GET /api/search
```

**Parâmetros:**
- `q` (opcional): Termo de busca (padrão: "agent based models")
- `source` (opcional): "openalex", "overton" ou "both" (padrão: "both")
- `limit` (opcional): Número de resultados por fonte (padrão: 10)

**Exemplo:**
```bash
curl "http://localhost:5000/api/search?q=agent%20based%20models&limit=5"
```

#### Obter Estatísticas
```
GET /api/stats
```

**Exemplo:**
```bash
curl "http://localhost:5000/api/stats"
```

#### Health Check
```
GET /api/health
```

**Exemplo:**
```bash
curl "http://localhost:5000/api/health"
```

## 🏗️ Estrutura do Projeto

```
teste/
├── app.py                      # Aplicação Flask principal
├── requirements.txt            # Dependências Python
├── .env.example               # Exemplo de configuração
├── .gitignore                 # Arquivos ignorados pelo Git
├── services/                  # Serviços de integração
│   ├── __init__.py
│   ├── openalex_service.py   # Cliente OpenAlex API
│   └── overton_service.py    # Cliente Overton API
├── templates/                 # Templates HTML
│   └── index.html            # Página principal
└── static/                    # Arquivos estáticos
    ├── style.css             # Estilos CSS
    └── script.js             # JavaScript frontend
```

## 🔑 Obtendo Chaves de API

### Overton API

1. Acesse [Overton.io](https://www.overton.io)
2. Entre em contato com support@overton.io para solicitar acesso à API
3. Verifique se a API está habilitada passando o mouse sobre "Export" na barra de ação
4. Se aparecer "Generate API call", você tem acesso

### OpenAlex

- Não requer chave de API
- Recomenda-se fornecer um email no parâmetro `mailto` para melhores rate limits
- Configure o email no arquivo `.env`

## ⚙️ Configurações e Limitações

### Rate Limits

- **OpenAlex**: 100.000 requisições por dia (sem autenticação), ilimitado com email no polite pool
- **Overton**: 1 requisição por segundo (implementado automaticamente no código)

### Dados Focados em Agent-Based Models

A aplicação é configurada por padrão para pesquisar sobre "agent based models", mas você pode:
- Modificar o termo de busca na interface
- Usar filtros adicionais nas consultas
- Adaptar os serviços para outros tópicos

## 🔍 Funcionalidades Inferidas Implementadas

1. **Busca Multi-fonte**: Integração simultânea de múltiplas bases de dados
2. **Filtros Inteligentes**: Seleção de fontes e quantidade de resultados
3. **Visualização Enriquecida**:
   - Badges para Open Access
   - Conceitos-chave com scores
   - Informações sobre impacto em políticas
4. **Estatísticas Agregadas**: Dashboard com métricas globais
5. **Rate Limiting**: Proteção automática contra excesso de requisições
6. **Tratamento de Erros**: Mensagens claras para problemas de configuração
7. **Design Responsivo**: Funciona em desktop, tablet e mobile

## 🐛 Resolução de Problemas

### Erro: "Overton API key not configured"

- Verifique se adicionou a chave no arquivo `.env`
- Certifique-se de que o arquivo `.env` está no diretório raiz
- Reinicie a aplicação após configurar

### Erro: "OpenAlex API error"

- Verifique sua conexão com a internet
- A API pode estar temporariamente indisponível
- Tente novamente após alguns segundos

### Nenhum resultado encontrado

- Tente termos de busca mais genéricos
- Verifique a ortografia
- Experimente buscar em apenas uma fonte por vez

## 📊 Exemplos de Uso

### Pesquisar trabalhos recentes sobre ABM

```python
# Via código Python
from services.openalex_service import OpenAlexService

service = OpenAlexService(email="seu@email.com")
results = service.search_works("agent based models", limit=20)

for work in results['works']:
    print(f"{work['title']} ({work['publication_year']})")
```

### Obter estatísticas de impacto político

```python
from services.overton_service import OvertonService

service = OvertonService(api_key="sua_chave")
stats = service.get_stats("agent based models")
print(f"Total de menções em políticas: {stats['total_policy_mentions']}")
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## 📝 Licença

Este projeto é fornecido como está, para fins educacionais e de pesquisa.

## 🔗 Links Úteis

- [OpenAlex Documentation](https://docs.openalex.org)
- [Overton API Documentation](https://help.overton.io/article/using-the-overton-api/)
- [Agent-Based Modeling Resources](https://en.wikipedia.org/wiki/Agent-based_model)

## 👥 Autores

Desenvolvido para pesquisa e exploração de Agent-Based Models na literatura acadêmica e documentos de política.

---

**Nota**: Esta aplicação foca em pesquisas sobre Agent-Based Models, mas pode ser facilmente adaptada para outros tópicos de pesquisa modificando os termos de busca padrão.