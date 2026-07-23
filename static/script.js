document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos da interface
    const geminiKeyInput = document.getElementById('geminiKey');
    const btnToggleKey = document.getElementById('btnToggleKey');
    
    // Inputs e previews
    const inputFoto = document.getElementById('inputFoto');
    const dropzoneFoto = document.getElementById('dropzoneFoto');
    const previewFoto = document.getElementById('previewFoto');
    const nomeFoto = document.getElementById('nomeFoto');
    const btnRemoverFoto = document.getElementById('btnRemoverFoto');

    const inputAudio = document.getElementById('inputAudio');
    const dropzoneAudio = document.getElementById('dropzoneAudio');
    const previewAudio = document.getElementById('previewAudio');
    const nomeAudio = document.getElementById('nomeAudio');
    const btnRemoverAudio = document.getElementById('btnRemoverAudio');

    const btnGerar = document.getElementById('btnGerar');
    const btnText = btnGerar.querySelector('.btn-text');
    const spinner = btnGerar.querySelector('.spinner');

    const alertBox = document.getElementById('alertBox');
    const resultCard = document.getElementById('resultCard');
    const resultBody = document.getElementById('resultBody');
    const btnCopiar = document.getElementById('btnCopiar');
    const copyText = document.getElementById('copyText');

    let ataGeradaTexto = '';

    // Alternar visibilidade da chave de API
    btnToggleKey.addEventListener('click', () => {
        const isPassword = geminiKeyInput.type === 'password';
        geminiKeyInput.type = isPassword ? 'text' : 'password';
        btnToggleKey.textContent = isPassword ? '🙈' : '👁️';
    });

    // Configuração dos eventos de Drag and Drop e File Selection
    setupFileHandler(inputFoto, dropzoneFoto, previewFoto, nomeFoto, btnRemoverFoto);
    setupFileHandler(inputAudio, dropzoneAudio, previewAudio, nomeAudio, btnRemoverAudio);

    function setupFileHandler(inputEl, dropzoneEl, previewEl, nameEl, removeBtnEl) {
        // Mudança via clique
        inputEl.addEventListener('change', (e) => {
            if (inputEl.files && inputEl.files[0]) {
                const file = inputEl.files[0];
                nameEl.textContent = file.name;
                previewEl.style.display = 'flex';
                dropzoneEl.classList.add('active');
            }
        });

        // Eventos Drag and Drop
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzoneEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneEl.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzoneEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneEl.classList.remove('dragover');
            });
        });

        dropzoneEl.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                inputEl.files = files;
                nameEl.textContent = files[0].name;
                previewEl.style.display = 'flex';
                dropzoneEl.classList.add('active');
            }
        });

        // Remover arquivo selecionado
        removeBtnEl.addEventListener('click', (e) => {
            e.stopPropagation();
            inputEl.value = '';
            previewEl.style.display = 'none';
            dropzoneEl.classList.remove('active');
        });
    }

    // Exibição de Alertas
    function mostrarErro(mensagem) {
        alertBox.textContent = mensagem;
        alertBox.className = 'alert alert-error';
        alertBox.style.display = 'block';
    }

    function ocultarErro() {
        alertBox.style.display = 'none';
        alertBox.textContent = '';
    }

    // Submissão e Chamada Assíncrona para a API
    btnGerar.addEventListener('click', async () => {
        ocultarErro();
        
        const key = geminiKeyInput.value.trim();

        const temFoto = inputFoto.files && inputFoto.files.length > 0;
        const temAudio = inputAudio.files && inputAudio.files.length > 0;

        if (!temFoto && !temAudio) {
            mostrarErro('Selecione pelo menos um arquivo (Foto das anotações ou Áudio da reunião).');
            return;
        }

        // Prepara o FormData para multipart/form-data
        const formData = new FormData();
        if (key) {
            formData.append('gemini_key', key);
        }
        if (temFoto) {
            formData.append('foto', inputFoto.files[0]);
        }
        if (temAudio) {
            formData.append('audio', inputAudio.files[0]);
        }

        // Ativa estado de carregamento
        setLoadingState(true);

        try {
            const response = await fetch('/api/gerar-ata', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Ocorreu um erro ao processar a ata de reunião.');
            }

            // Sucesso!
            ataGeradaTexto = data.ata;
            renderizarAta(ataGeradaTexto);
            resultCard.style.display = 'flex';
            resultCard.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            mostrarErro(err.message || 'Falha de comunicação com o servidor.');
        } finally {
            setLoadingState(false);
        }
    });

    function setLoadingState(isLoading) {
        if (isLoading) {
            btnGerar.disabled = true;
            btnText.textContent = 'Processando com Gemini AI...';
            spinner.style.display = 'inline-block';
        } else {
            btnGerar.disabled = false;
            btnText.textContent = '⚡ Gerar Ata com Gemini 1.5 Flash';
            spinner.style.display = 'none';
        }
    }

    // Renderização simples e limpa do resultado em Markdown
    function renderizarAta(markdown) {
        // Converte tabelas e headers básicos do Markdown em HTML simples para exibição agradável
        let html = markdown
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Formatando headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Strong/Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        resultBody.innerHTML = html;
    }

    // Copiar Texto para Área de Transferência
    btnCopiar.addEventListener('click', async () => {
        if (!ataGeradaTexto) return;
        try {
            await navigator.clipboard.writeText(ataGeradaTexto);
            copyText.textContent = 'Copiado!';
            btnCopiar.style.borderColor = 'var(--success-color)';
            setTimeout(() => {
                copyText.textContent = 'Copiar Ata';
                btnCopiar.style.borderColor = 'var(--border-color)';
            }, 2000);
        } catch (err) {
            console.error('Erro ao copiar texto: ', err);
        }
    });
});
