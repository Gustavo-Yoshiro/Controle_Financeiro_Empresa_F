🏠 Sistema de Gestão Família Enterprise

📌 Sobre o Projeto

O que a aplicação faz?
O Sistema de Gestão Família Enterprise é uma plataforma completa (estilo SaaS) desenvolvida para centralizar a administração de propriedades (Kitnets), o fluxo de caixa financeiro (Cartões de Crédito, Boletos, Empréstimos) e a gestão de frota e logística.

Por que foi construído?
Construído para substituir folhas de cálculo manuais e processos descentralizados, garantindo uma visão real do patrimônio da família. O sistema calcula automaticamente o "poder de compra real" (abatendo dívidas futuras projetadas) e conta com um robô autônomo que gera as faturas de aluguer mensalmente.

Com o que foi construído?

Frontend/UI: Streamlit (para uma interface web fluida e reativa).

Backend/Lógica: Python (arquitetura MVC limpa e orientada a serviços).

Banco de Dados: SQLite (leve e embutido, mas preparado para migração futura).

🚀 Instruções de Instalação

Para correr este projeto na tua máquina local, precisarás ter o Python 3.9+ e o pip instalados.

1. Clonar o repositório:

git clone [https://github.com/Gustavo-Yoshiro/nome-do-repositorio.git](https://github.com/Gustavo-Yoshiro/Controle_Financeiro_Empresa_F.git)
cd Controle_Financeiro_Empresa_F


2. Criar e ativar um ambiente virtual (Recomendado):

python -m venv venv

# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate


3. Instalar as dependências do projeto:

pip install streamlit pandas python-dateutil streamlit-option-menu


4. Configurar as chaves de segurança:
Cria uma pasta chamada .streamlit na raiz do projeto e um ficheiro secrets.toml dentro dela:

mkdir .streamlit
touch .streamlit/secrets.toml


Adiciona a palavra-passe mestra do sistema dentro do ficheiro secrets.toml:

senha_sistema = "sua_senha_secreta"


💻 Instruções de Uso

Após concluir a instalação, podes iniciar o servidor local do Streamlit executando o seguinte comando no terminal:

streamlit run UI/App.py


O teu navegador padrão vai abrir automaticamente no endereço http://localhost:8501.

No ecrã de bloqueio, insere a palavra-passe que configuraste no passo anterior.

Navega pelo menu lateral para aceder aos painéis de Kitnets, Dívidas & Boletos ou Financeiro.

Nota: Na primeira vez que correres o projeto, o ficheiro do banco de dados banco_dados.db e as pastas de uploads (uploads_contratos/ e uploads_comprovantes/) serão criados automaticamente.

🤝 Como Contribuir

Se desejas contribuir para a melhoria deste sistema (seja resolvendo um bug ou criando uma nova funcionalidade), segue os passos abaixo:

Faz um Fork do projeto.

Cria uma nova branch com a tua feature: git checkout -b minha-feature

Guarda as tuas alterações e cria um commit descrevendo o que fizeste: git commit -m "feat: adicionado filtro por data no financeiro"

Faz o push para a tua branch: git push origin minha-feature

Abre um Pull Request detalhando as tuas mudanças.

🔒 Boas Práticas (Aviso de Segurança)

Se fores alojar este repositório de forma pública, NÃO faças commit de ficheiros sensíveis. O ficheiro .gitignore já deve estar configurado para ignorar:

venv/ e __pycache__/

.streamlit/secrets.toml (As tuas palavras-passe)

banco_dados.db (Os teus dados financeiros e de inquilinos reais)

Diretórios uploads_contratos/ e uploads_comprovantes/

👤 Autor

Criado e mantido por Gustavo Saito.

GitHub: @Gustavo-Yoshiro

LinkedIn: gustavosaitodev

