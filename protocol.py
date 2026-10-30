# define o protocolo de comunicacao entre cliente e servidor
#as mensagens sao separadas por | e terminadas em \n
#quando ha transferencia de arquivos, o tamanho e informado antes dos bytes

SEPARADOR = "|"
LIMITE_LINHA = 4096 


def montar(*campos):
    """Junta os campos com | para formar uma linha. Ex: montar("OK", 12) -> "OK|12"."""
    return SEPARADOR.join(str(c) for c in campos)


def enviar_linha(sock, texto):
    """Manda uma linha de texto terminada em \\n."""
    sock.sendall((texto + "\n").encode("utf-8"))


def receber_linha(sock):
    """Le uma linha, ate o \\n, e devolve como texto (sem o \\n).

    Le 1 BYTE POR VEZ de proposito: se lesse 4096 de uma vez, poderia pegar
    junto os primeiros bytes da imagem que vem logo depois do comando e perde-los.
    A linha de comando tem poucos bytes, entao a lentidao nao pesa.
    """
    dados = b""
    while True:
        byte = sock.recv(1)
        if byte == b"":
            # recv vazio = o outro lado fechou a conexao
            raise ConnectionError("conexao encerrada")
        if byte == b"\n":
            break
        dados += byte
        if len(dados) > LIMITE_LINHA:
            raise ValueError("linha muito longa")
    return dados.decode("utf-8", errors="replace").rstrip("\r")


def receber_exato(sock, n):
    """Le EXATAMENTE n bytes.

    recv(4096) devolve ate 4096 bytes, nao exatamente 4096. Com uma imagem grande
    os dados chegam em pedacos, entao juntamos os pedacos num loop ate completar n.
    """
    partes = []
    faltam = n
    while faltam > 0:
        pedaco = sock.recv(min(faltam, 4096))
        if pedaco == b"":
            raise ConnectionError("conexao caiu antes de receber tudo")
        partes.append(pedaco)
        faltam -= len(pedaco)
    return b"".join(partes)


def enviar_arquivo(sock, dados):
    """Manda os bytes do arquivo (o tamanho ja foi informado na linha anterior)."""
    sock.sendall(dados)