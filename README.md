# Repositório colaborativo de imagens

Aplicação cliente-servidor em Python que compartilha imagens por TCP. O servidor valida e armazena os arquivos, gera miniaturas JPEG de até 128 × 128 pixels e registra metadados e ações em SQLite.

## Requisitos

- Python 3.10 ou superior
- Pillow (instalado pelo `requirements.txt`)

## Instalação

Na pasta do projeto, crie e ative um ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No macOS ou Linux, ative o ambiente com `source .venv/bin/activate`.

## Execução

Abra um terminal para iniciar o servidor:

```text
python server.py
```

O servidor escuta na porta TCP 5000 em todas as interfaces. Em outro terminal, inicie o cliente:

```text
python client.py [host] [porta]
```

Sem argumentos, o cliente conecta a `127.0.0.1:5000`. Para conectar de outro computador, informe o endereço IP do servidor e permita conexões TCP nessa porta na rede/firewall.

## Comandos do cliente

- **Login**: cria a conta no primeiro acesso ou autentica uma conta existente. É opcional; sem login, as imagens ficam atribuídas a `anonimo`.
- **UPLOAD**: envia uma imagem de até 20 MiB. Extensões aceitas: JPG, JPEG, PNG, GIF, BMP e WebP.
- **LIST**: lista ID, nome original, autor, data e tamanho.
- **DOWNLOAD**: salva o original na pasta `downloads/`.
- **VIEW**: salva e tenta abrir a miniatura JPEG na pasta `downloads/`.
- **HIST**: exibe as 20 ações mais recentes.

DOWNLOAD e VIEW aceitam ID ou nome; se um nome estiver repetido, é escolhida a imagem mais recente. O cliente e o servidor usam linhas UTF-8 terminadas em `\n`, com campos separados por `|`; transferências binárias informam o tamanho antes dos bytes.

## Arquivos e dados

- `server.py`: servidor TCP e atendimento concorrente
- `client.py`: menu de terminal
- `protocol.py`: mensagens de texto e transferências de tamanho conhecido
- `storage.py`: validação, IDs SHA-256, originais e miniaturas
- `database.py`: usuários, imagens e histórico em `repository.db`
- `uploads/<usuario>/`: imagens originais
- `thumbnails/<usuario>/`: miniaturas JPEG

O ID usa os 12 primeiros caracteres hexadecimais do SHA-256 do conteúdo e também permite detectar imagens repetidas. Não há verificação de hash fim a fim da transferência. As senhas são armazenadas como SHA-256 sem salt, uma simplificação acadêmica que não deve ser usada como modelo para autenticação em produção.

O banco e os arquivos enviados são criados durante a execução e ignorados pelo Git. Para testar sem misturar dados, use uma cópia temporária do projeto ou remova `repository.db`, `uploads/` e `thumbnails/` com o servidor parado.
