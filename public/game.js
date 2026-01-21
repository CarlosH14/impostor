// Configuración de la API
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin;

// Variables globales
let gameId = localStorage.getItem('gameId');
let playerId = localStorage.getItem('playerId');
let playerName = localStorage.getItem('playerName');
let isHost = localStorage.getItem('isHost') === 'true';
let updateInterval;
let currentRoundNumber = 0; // Trackear el número de ronda actual

// Elementos del DOM
const gameCodeElement = document.getElementById('gameCode');
const copyCodeBtn = document.getElementById('copyCodeBtn');
const waitingRoom = document.getElementById('waitingRoom');
const gameInProgress = document.getElementById('gameInProgress');
const currentPlayersElement = document.getElementById('currentPlayers');
const maxPlayersElement = document.getElementById('maxPlayers');
const playersListElement = document.getElementById('playersList');
const hostActions = document.getElementById('hostActions');
const startRoundBtn = document.getElementById('startRoundBtn');
const leaveGameBtn = document.getElementById('leaveGameBtn');
const revealWordBtn = document.getElementById('revealWordBtn');
const wordReveal = document.getElementById('wordReveal');
const wordDisplay = document.getElementById('wordDisplay');
const playerWordElement = document.getElementById('playerWord');
const roleTextElement = document.getElementById('roleText');
const gamePlayersListElement = document.getElementById('gamePlayersList');
const loadingModal = document.getElementById('loadingModal');

// Verificar que tengamos los datos necesarios
if (!gameId || !playerId || !playerName) {
    alert('No se encontró información de la partida. Redirigiendo...');
    window.location.href = '/';
}

// Mostrar código de partida
gameCodeElement.textContent = gameId.substring(0, 8).toUpperCase();

// Copiar código
copyCodeBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(gameId).then(() => {
        alert('✅ Código copiado al portapapeles');
    });
});

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

// Manejar nueva ronda
function handleNewRound() {
    console.log('🔄 Reseteando vista para nueva ronda...');
    
    // Resetear vista de palabra
    wordReveal.style.display = 'block';
    wordDisplay.style.display = 'none';
    
    // Limpiar contenido previo
    playerWordElement.textContent = '';
    roleTextElement.textContent = '';
    
    // Limpiar pista si existe
    const hintBox = wordDisplay.querySelector('.hint-box');
    if (hintBox) {
        hintBox.remove();
    }
    
    // Ocultar botones de control hasta que se revele la palabra
    const gameActions = document.getElementById('gameActions');
    gameActions.style.display = 'none';
    
    // Mostrar notificación al jugador
    alert('🎲 ¡Nueva ronda iniciada! Presiona el botón para revelar tu nueva palabra.');
}

// Función para cargar y mostrar la palabra (reutilizable)
async function loadAndShowWord() {
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/game/get-word`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_id: gameId,
                player_id: playerId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al obtener la palabra');
        }
        
        const data = await response.json();
        
        hideLoading();
        
        // Mostrar palabra
        wordReveal.style.display = 'none';
        wordDisplay.style.display = 'block';
        
        playerWordElement.textContent = data.word;
        
        if (data.is_impostor) {
            roleTextElement.textContent = '⚠️ ¡Eres el IMPOSTOR! Descubre cuál es la palabra real sin ser descubierto.';
            roleTextElement.style.color = '#ef4444';
            
            // Mostrar pista si está disponible
            if (data.hint) {
                const hintElement = document.createElement('div');
                hintElement.className = 'hint-box';
                hintElement.innerHTML = `
                    <strong>💡 Pista:</strong> ${data.hint}
                `;
                wordDisplay.appendChild(hintElement);
            }
        } else {
            roleTextElement.textContent = '✓ Eres un jugador normal. Descubre quién es el impostor.';
            roleTextElement.style.color = '#10b981';
        }
        
        // Mostrar botones de control SOLO si es host
        const gameActions = document.getElementById('gameActions');
        if (isHost) {
            gameActions.style.display = 'flex';
        } else {
            gameActions.style.display = 'none';
        }
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Actualizar estado del juego
async function updateGameState() {
    try {
        const response = await fetch(`${API_URL}/game/${gameId}`);
        
        if (!response.ok) {
            throw new Error('Error al obtener el estado del juego');
        }
        
        const game = await response.json();
        
        // Detectar cambio de ronda
        if (game.round_number > currentRoundNumber && currentRoundNumber > 0) {
            console.log(`🔄 Nueva ronda detectada: ${currentRoundNumber} -> ${game.round_number}`);
            handleNewRound();
        }
        currentRoundNumber = game.round_number;
        
        // Actualizar contador de jugadores
        currentPlayersElement.textContent = game.players.length;
        maxPlayersElement.textContent = game.max_players;
        
        // Actualizar lista de jugadores
        playersListElement.innerHTML = '';
        game.players.forEach((player, index) => {
            const playerItem = document.createElement('div');
            playerItem.className = 'player-item';
            if (index === 0) playerItem.classList.add('host');
            
            playerItem.innerHTML = `
                <div class="player-avatar">${player.name.charAt(0).toUpperCase()}</div>
                <div class="player-info">
                    <div class="player-name">${player.name}</div>
                    ${index === 0 ? '<div class="player-badge">👑 HOST</div>' : ''}
                </div>
            `;
            
            playersListElement.appendChild(playerItem);
        });
        
        // Mostrar acciones del host si es necesario
        if (isHost && game.status === 'waiting') {
            hostActions.style.display = 'block';
            document.getElementById('waitingMessage').textContent = 
                game.players.length >= 3 
                    ? '¡Ya puedes iniciar la ronda!' 
                    : `Necesitas al menos ${3 - game.players.length} jugador(es) más`;
            
            startRoundBtn.disabled = game.players.length < 3;
        }
        
        // Si el juego está en progreso, cambiar de vista
        if (game.status === 'in_progress') {
            // Solo cambiar de vista si aún no lo hemos hecho
            if (waitingRoom.style.display !== 'none') {
                waitingRoom.style.display = 'none';
                gameInProgress.style.display = 'block';
            }
            
            // NO detener el polling - necesitamos seguir detectando cambios de ronda
            // clearInterval(updateInterval); // REMOVIDO para permitir detección de nuevas rondas
            
            // Actualizar lista de jugadores en juego
            gamePlayersListElement.innerHTML = '';
            game.players.forEach(player => {
                const playerItem = document.createElement('div');
                playerItem.className = 'player-item';
                playerItem.innerHTML = `
                    <div class="player-avatar">${player.name.charAt(0).toUpperCase()}</div>
                    <div class="player-info">
                        <div class="player-name">${player.name}</div>
                    </div>
                `;
                gamePlayersListElement.appendChild(playerItem);
            });
            
            // Mostrar botones de control SOLO si es host
            const gameActions = document.getElementById('gameActions');
            if (isHost && wordDisplay.style.display === 'block') {
                gameActions.style.display = 'flex';
            }
        }
        
    } catch (error) {
        console.error('Error al actualizar el estado:', error);
    }
}

// Iniciar ronda
startRoundBtn.addEventListener('click', async () => {
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/game/start-round`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_id: gameId,
                player_id: playerId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al iniciar la ronda');
        }
        
        hideLoading();
        await updateGameState();
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
});

// Revelar palabra
revealWordBtn.addEventListener('click', async () => {
    await loadAndShowWord();
});

// Siguiente Ronda
const nextRoundBtn = document.getElementById('nextRoundBtn');
if (nextRoundBtn) {
    nextRoundBtn.addEventListener('click', async () => {
        if (!confirm('¿Iniciar una nueva ronda? Todos recibirán nuevas palabras.')) {
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`${API_URL}/game/start-round`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    game_id: gameId,
                    player_id: playerId
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Error al iniciar nueva ronda');
            }
            
            hideLoading();
            
            // El reset se manejará automáticamente cuando se detecte el cambio de round_number
            // en updateGameState()
            
        } catch (error) {
            hideLoading();
            showError(error.message);
        }
    });
}

// Finalizar Partida
const endGameBtn = document.getElementById('endGameBtn');
if (endGameBtn) {
    endGameBtn.addEventListener('click', async () => {
        if (!confirm('¿Estás seguro de que quieres finalizar la partida? Todos los jugadores serán desconectados.')) {
            return;
        }
        
        showLoading();
        
        try {
            const response = await fetch(`${API_URL}/game/${gameId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Error al finalizar la partida');
            }
            
            hideLoading();
            
            alert('🏁 Partida finalizada. ¡Gracias por jugar!');
            
            // Limpiar localStorage
            localStorage.removeItem('gameId');
            localStorage.removeItem('playerId');
            localStorage.removeItem('playerName');
            localStorage.removeItem('isHost');
            
            // Redirigir al inicio
            window.location.href = '/';
            
        } catch (error) {
            hideLoading();
            showError(error.message);
        }
    });
}

// Salir del juego
leaveGameBtn.addEventListener('click', () => {
    if (confirm('¿Estás seguro de que quieres salir del juego?')) {
        localStorage.removeItem('gameId');
        localStorage.removeItem('playerId');
        localStorage.removeItem('playerName');
        localStorage.removeItem('isHost');
        window.location.href = '/';
    }
});

// Iniciar actualización periódica
updateGameState();
updateInterval = setInterval(updateGameState, 2000); // Actualizar cada 2 segundos
