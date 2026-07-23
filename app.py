import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from gemini_service import processar_ata_multimodal
from image_service import comprimir_imagem
from supabase_service import SupabaseService

app = FastAPI(
    title="Gerador de Atas de Reunião com Gemini AI",
    description="Backend de alta performance para conversão de anotações e áudios em atas executivas.",
    version="1.0.0"
)

# Inicializa o serviço do Supabase
supabase_service = SupabaseService()

# Monta o diretório estático para os assets do frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    """Servidor da página principal index.html"""
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Arquivo index.html não encontrado no diretório static.")
    return FileResponse(index_path)

@app.post("/api/gerar-ata")
async def gerar_ata(
    foto: Optional[UploadFile] = File(None, description="Foto manuscrita ou do quadro da reunião"),
    audio: Optional[UploadFile] = File(None, description="Gravação de áudio da reunião")
):
    """
    Endpoint principal para recebimento dos arquivos e processamento via Gemini 2.5 Flash.
    A chave de API é carregada automaticamente do arquivo .env pelo gemini_service.
    """
    bytes_imagem: Optional[bytes] = None
    bytes_audio: Optional[bytes] = None
    mime_audio: str = "audio/mp3"

    # Processamento da Foto (Compressão via Pillow)
    if foto and foto.filename:
        conteudo_foto = await foto.read()
        if conteudo_foto:
            try:
                bytes_imagem = comprimir_imagem(conteudo_foto, qualidade=60, max_dimensao=1600)
            except Exception as err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Erro ao comprimir a imagem enviada: {str(err)}"
                )

    # Processamento do Áudio
    if audio and audio.filename:
        bytes_audio = await audio.read()
        if audio.content_type:
            mime_audio = audio.content_type

    # Validação de recebimento de ao menos UM arquivo válido
    if not bytes_imagem and not bytes_audio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="É necessário enviar pelo menos uma foto das anotações ou o áudio da reunião."
        )

    # Invocação do Serviço Gemini
    try:
        ata_markdown = processar_ata_multimodal(
            bytes_imagem=bytes_imagem,
            bytes_audio=bytes_audio,
            mime_audio=mime_audio
        )
    except ValueError as val_err:
        # Mensagens amigáveis já formatadas pelo gemini_service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível processar os arquivos e gerar a ata. Verifique se o áudio/imagem está em um formato válido."
        )

    # Persistência Opcional no Supabase (se configurado)
    try:
        supabase_service.salvar_ata(
            titulo="Ata de Reunião Gerada",
            conteudo_markdown=ata_markdown,
            metadata={"tem_foto": bool(foto), "tem_audio": bool(audio)}
        )
    except Exception:
        # Erro no Supabase não deve travar a resposta para o usuário
        pass

    return JSONResponse(
        status_code=200,
        content={
            "sucesso": True,
            "ata": ata_markdown
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
