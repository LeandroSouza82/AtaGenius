"""Módulo de integração com a API do Google Gemini AI."""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


PROMPT_ATA_NOTARIAL = """
Você é um redator jurídico e corporativo especializado na confecção de atas formais para registro em cartório e assembleias formais.

Analise os materiais fornecidos (áudio gravado da reunião e/ou foto das anotações manuscritas) e elabore a minuta formal da ATA DE REUNIÃO.

REGRAS DE REDAÇÃO E VALIDADE FORMAL:
1. Linguagem: Culta, formal, impessoal e no tempo verbal do pretérito perfeito do indicativo.
2. Fidelidade: Transcreva rigorosamente apenas os fatos, discussões, deliberações e votações que constarem nos materiais. Não invente ou presuma informações.
3. Tratamento de Lacunas: Caso algum dado obrigatório (como horário exato de término ou lista completa de qualificações) não conste nos arquivos, utilize colchetes explicativos como [A preencher na assinatura] ou [Nome legível do participante].

ESTRUTURA OBRIGATÓRIA DA ATA (FORMATO MARKDOWN):

# ATA DA REUNIÃO [TÍTULO/PROPÓSITO DA REUNIÃO]

**1. DATA, HORÁRIO E LOCAL:**
- **Data:** [Data identificada ou preencher]
- **Horário de Início:** [Horário de início] | **Término:** [Horário de encerramento]
- **Local/Plataforma:** [Endereço físico ou link/plataforma virtual]

**2. CONVOCAÇÃO E PRESENÇAS:**
- **Presidente da Mesa:** [Nome / Qualificação]
- **Secretário(a):** [Nome / Qualificação]
- **Participantes Presentes:** [Lista formal de participantes identificados]

**3. ORDEM DO DIA (PAUTA):**
[Enumeração clara dos tópicos/pautas discutidos]

**4. DELIBERAÇÕES E DISCUSSÕES:**
[Relato detalhado e cronológico do que foi discutido, propostas apresentadas, consensos atingidos e resultados de eventuais votações]

**5. PLANO DE AÇÃO E OBRIGAÇÕES (SE HOUVER):**
| Item | Descrição da Ação / Compromisso | Responsável | Prazo Final |
| :--- | :--- | :--- | :--- |

**6. ENCERRAMENTO E LAVRATURA:**
Nada mais havendo a tratar, a reunião foi encerrada, do que se lavrou a presente ata que, lida e achada conforme, vai assinada pelos presentes para que surta seus efeitos legais e seja levada a registro perante o Cartório de Títulos e Documentos competente.

---
**ASSINATURAS DOS PRESENTES:**

_______________________________________
[Nome do Presidente da Mesa]

_______________________________________
[Nome do Secretário]
"""


def processar_ata_multimodal(
    api_key: str | None = None,
    bytes_imagem: bytes | None = None,
    bytes_audio: bytes | None = None,
    mime_audio: str = "audio/mp3",
) -> str:
    """Gera uma ata executiva em Markdown a partir de imagem e/ou áudio."""
    key = (api_key or "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "Cole_Sua_Chave_Aqui":
        raise ValueError(
            "A chave da API do Gemini é obrigatória. Forneça a chave ou configure GEMINI_API_KEY no arquivo .env."
        )

    if not bytes_imagem and not bytes_audio:
        raise ValueError("É necessário fornecer pelo menos uma foto das anotações ou o áudio da reunião.")

    client = genai.Client(api_key=key)

    contents = [PROMPT_ATA_NOTARIAL]

    if bytes_imagem:
        contents.append(
            types.Part.from_bytes(data=bytes_imagem, mime_type="image/jpeg"),
        )

    if bytes_audio:
        contents.append(
            types.Part.from_bytes(data=bytes_audio, mime_type=mime_audio),
        )

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=contents,
    )
    return response.text

