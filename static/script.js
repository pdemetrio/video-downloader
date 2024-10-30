// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const downloadForm = document.getElementById('download-form');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress');
    const progressText = document.getElementById('progress-text');
    const statusMessage = document.getElementById('status-message');
    const cancelButton = document.getElementById('cancel-button');
    let eventSource = null;

    downloadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        // Reset UI elements
        progressContainer.style.display = 'block';
        cancelButton.style.display = 'block';
        statusMessage.textContent = '';
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        
        document.getElementById('download-button').disabled = true;

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started') {
                if (eventSource) {
                    eventSource.close();
                }
                
                eventSource = new EventSource('/progress');
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.status === 'Cancelado') {
                        statusMessage.textContent = 'Download cancelado!';
                        cancelButton.style.display = 'none';
                        document.getElementById('download-button').disabled = false;
                        eventSource.close();
                        return;
                    }
                    
                    if (data.status === 'Erro') {
                        statusMessage.textContent = 'Erro no download!';
                        cancelButton.style.display = 'none';
                        document.getElementById('download-button').disabled = false;
                        eventSource.close();
                        return;
                    }

                    // Atualiza a barra de progresso visualmente
                    let percentage = parseFloat(data.percentage.replace('%', ''));
                    progressBar.style.width = `${percentage}%`;
                    progressBar.textContent = `${percentage.toFixed(1)}%`;
                    // Força o navegador a renderizar a mudança
                    progressBar.offsetHeight;

                    if (data.status === 'Concluído') {
                        progressText.textContent = 'Download Completo!';
                        statusMessage.textContent = 'Download concluído com sucesso!';
                        cancelButton.style.display = 'none';
                        document.getElementById('download-button').disabled = false;
                        eventSource.close();
                    } else {
                        progressText.textContent = `Velocidade: ${data.speed || 'N/A'}, ETA: ${data.eta || 'N/A'}`;
                    }
                };

                eventSource.onerror = function() {
                    eventSource.close();
                    document.getElementById('download-button').disabled = false;
                };
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            statusMessage.textContent = 'Erro ao iniciar o download!';
            document.getElementById('download-button').disabled = false;
        });
    });

    cancelButton.addEventListener('click', function() {
        fetch('/cancel_download', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'canceling') {
                statusMessage.textContent = 'Cancelando download...';
            }
        })
        .catch(error => {
            console.error('Erro ao cancelar:', error);
            statusMessage.textContent = 'Erro ao cancelar o download!';
        });
    });
});