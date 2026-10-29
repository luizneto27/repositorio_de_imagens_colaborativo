Sistema distribuído cliente-servidor com Sockets TCP para compartilhamento colaborativo de imagens. Permite upload, armazenamento, listagem, visualização por miniaturas e download, mantendo um histórico com informações sobre autoria, data de envio e tamanho dos arquivos.


## TECNOLOGIAS A SEREM USADAS: 

socket: comunicacao TCP
threading: atendimento simultaneo de clientes
os e pathlib: Gerenciamento de arquivos e diretórios
json: Organização de metadados
hashlib: cálculo de hashes e verificação de integridade
Pillow: geração de miniatura
algum banco de dados

COMANDOS DO SISTEMA:

| Comando    | Função                     | Resposta esperada            |
| ---------- | -------------------------- | ---------------------------- |
| `UPLOAD`   | Enviar uma imagem          | Confirmação do armazenamento |
| `LIST`     | Listar imagens disponíveis | Lista de metadados           |
| `DOWNLOAD` | Baixar uma imagem original | Tamanho e bytes da imagem    |
| `VIEW`     | Obter uma miniatura        | Tamanho e bytes da miniatura |


RESPONSABILIDADE DE CADA ARQUIVO: 

| Arquivo ou diretório | Responsabilidade                         |
| -------------------- | ---------------------------------------- |
| `server.py`          | Criar o servidor TCP e atender clientes  |
| `client.py`          | Conectar ao servidor e executar comandos |
| `protocol.py`        | Definir o formato das mensagens          |
| `storage.py`         | Salvar, localizar e recuperar imagens    |
| `database.py`        | Registrar usuários, arquivos e histórico |
| `uploads/`           | Armazenar as imagens originais           |
| `thumbnails/`        | Armazenar as miniaturas                  |
| `repository.db`      | Guardar os metadados no SQLite           |
| `README.md`          | Documentar a instalação e a utilização   |


