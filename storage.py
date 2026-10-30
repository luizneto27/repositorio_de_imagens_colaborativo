"""Validação e armazenamento das imagens originais do repositório."""

import hashlib
import io
from pathlib import Path

from PIL import Image


PASTA = Path(__file__).resolve().parent
PASTA_UPLOADS = PASTA / "uploads"
TAMANHO_MAXIMO = 20 * 1024 * 1024
EXTENSOES_VALIDAS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def limpar_nome(nome):
    """Retorna apenas o nome do arquivo e recusa nomes inválidos no protocolo."""
    if not isinstance(nome, str):
        raise ValueError("nome do arquivo inválido")

    # Tratar separadores dos dois sistemas operacionais, mesmo quando o servidor
    # recebe um nome criado em outro sistema.
    nome = nome.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not nome or nome in {".", ".."} or "|" in nome or "\x00" in nome:
        raise ValueError("nome do arquivo inválido")
    return nome


def extensao_valida(nome):
    """Informa se o nome possui uma extensão de imagem aceita."""
    try:
        nome = limpar_nome(nome)
    except ValueError:
        return False
    return Path(nome).suffix.lower() in EXTENSOES_VALIDAS


def _bytes_arquivo(arquivo):
    """Converte bytes ou um caminho para o conteúdo do arquivo."""
    if isinstance(arquivo, (bytes, bytearray, memoryview)):
        return bytes(arquivo)
    with open(arquivo, "rb") as entrada:
        return entrada.read()


def eh_imagem(arquivo):
    """Valida o conteúdo com Pillow, sem confiar apenas na extensão."""
    try:
        conteudo = _bytes_arquivo(arquivo)
        if not conteudo or len(conteudo) > TAMANHO_MAXIMO:
            return False
        with Image.open(io.BytesIO(conteudo)) as imagem:
            imagem.verify()
        return True
    except (OSError, ValueError, TypeError, Image.DecompressionBombError):
        return False


def gerar_id(conteudo):
    """Gera o identificador com os 12 primeiros caracteres do SHA-256."""
    if not isinstance(conteudo, (bytes, bytearray, memoryview)):
        raise TypeError("o conteúdo deve ser bytes")
    return hashlib.sha256(conteudo).hexdigest()[:12]


def _limpar_usuario(usuario):
    if not isinstance(usuario, str):
        raise ValueError("usuário inválido")
    usuario = usuario.strip()
    if (not usuario or usuario in {".", ".."} or "|" in usuario
            or "/" in usuario or "\\" in usuario or "\x00" in usuario):
        raise ValueError("usuário inválido")
    return usuario


def salvar_imagem(usuario, nome, conteudo):
    """Valida e grava uma imagem original em uploads/<usuario>/<id><extensão>.

    Retorna (id, nome_original, tamanho, caminho). Rejeita arquivos inválidos,
    maiores que 20 MiB e conteúdo já armazenado.
    """
    usuario = _limpar_usuario(usuario)
    nome = limpar_nome(nome)
    if not extensao_valida(nome):
        raise ValueError("extensão de imagem inválida")
    if not isinstance(conteudo, (bytes, bytearray, memoryview)):
        raise TypeError("o conteúdo deve ser bytes")
    conteudo = bytes(conteudo)
    if len(conteudo) > TAMANHO_MAXIMO:
        raise ValueError("imagem excede o limite de 20 MB")
    if not eh_imagem(conteudo):
        raise ValueError("arquivo não contém uma imagem válida")

    id_img = gerar_id(conteudo)
    pasta_usuario = PASTA_UPLOADS / usuario
    pasta_usuario.mkdir(parents=True, exist_ok=True)
    caminho = pasta_usuario / (id_img + Path(nome).suffix.lower())
    # O identificador é global no banco; bloquear duplicatas também entre usuários
    # e extensões diferentes evita colisão com a chave primária de imagens.
    if any(PASTA_UPLOADS.glob(f"*/{id_img}.*")):
        raise ValueError("esta imagem já foi enviada")
    try:
        # Modo exclusivo: uma imagem repetida não sobrescreve o arquivo existente.
        with caminho.open("xb") as saida:
            saida.write(conteudo)
    except FileExistsError as erro:
        raise ValueError("esta imagem já foi enviada") from erro
    return id_img, nome, len(conteudo), str(caminho)


def ler_arquivo(caminho):
    """Lê e devolve os bytes de um arquivo armazenado."""
    with open(caminho, "rb") as arquivo:
        return arquivo.read()
