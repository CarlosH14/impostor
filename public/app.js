// Configuración de la API
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin;

// Elementos del DOM
const createGameForm = document.getElementById('createGameForm');
const joinGameForm = document.getElementById('joinGameForm');
const loadingModal = document.getElementById('loadingModal');

// Funciones de utilidad
function showLoading() {
    loadingModal.classList.add('active');
}

function hideLoading() {
    loadingModal.classList.remove('active');
}

function showError(message) {
    alert('❌ Error: ' + message);
}

function showSuccess(message) {
    alert('✅ ' + message);
}

// Crear partida
createGameForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('hostName').value.trim();
    const maxPlayers = parseInt(document.getElementById('maxPlayers').value);
    
    if (!name) {
        showError('Por favor ingresa tu nombre');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/game/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_name: name,
                max_players: maxPlayers
            })
        });
        
        if (!response.ok) {
            let errorMsg = 'Error al crear la partida';
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const error = await response.json();
                    errorMsg = error.detail || errorMsg;
                } else {
                    errorMsg = await response.text() || errorMsg;
                }
            } catch (e) {
                errorMsg = `Error ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        
        // Guardar información en localStorage
        localStorage.setItem('gameId', data.game_id);
        localStorage.setItem('playerId', data.players[0].player_id);
        localStorage.setItem('playerName', name);
        localStorage.setItem('isHost', 'true');
        
        // Redirigir a la sala de juego
        window.location.href = '/game.html';
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
});

// Unirse a partida
joinGameForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('playerName').value.trim();
    const gameId = document.getElementById('gameId').value.trim();
    
    if (!name || !gameId) {
        showError('Por favor completa todos los campos requeridos');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/game/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_name: name,
                game_id: gameId
            })
        });
        
        if (!response.ok) {
            let errorMsg = 'Error al unirse a la partida';
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const error = await response.json();
                    errorMsg = error.detail || errorMsg;
                } else {
                    errorMsg = await response.text() || errorMsg;
                }
            } catch (e) {
                errorMsg = `Error ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        
        // Buscar el ID del jugador que acaba de unirse
        const newPlayer = data.players.find(p => p.name === name);
        
        // Guardar información en localStorage
        localStorage.setItem('gameId', gameId);
        localStorage.setItem('playerId', newPlayer.player_id);
        localStorage.setItem('playerName', name);
        localStorage.setItem('isHost', 'false');
        
        // Redirigir a la sala de juego
        window.location.href = '/game.html';
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
});
