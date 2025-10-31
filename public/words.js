// Configuración de la API
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin;

// Elementos del DOM
const addWordForm = document.getElementById('addWordForm');
const wordsListElement = document.getElementById('wordsList');
const wordsCountElement = document.getElementById('wordsCount');
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

// Cargar todas las palabras
async function loadWords() {
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/words`);
        
        if (!response.ok) {
            throw new Error('Error al cargar las palabras');
        }
        
        const words = await response.json();
        
        hideLoading();
        
        // Actualizar contador
        wordsCountElement.textContent = `Total: ${words.length} palabra(s) disponible(s)`;
        
        // Limpiar lista
        wordsListElement.innerHTML = '';
        
        if (words.length === 0) {
            wordsListElement.innerHTML = '<p class="info-text">No hay palabras disponibles. ¡Agrega algunas!</p>';
            return;
        }
        
        // Agregar palabras a la lista
        words.forEach(wordData => {
            const wordItem = document.createElement('div');
            wordItem.className = 'word-item';
            wordItem.innerHTML = `
                <div class="word-header">
                    <h3>${wordData.word}</h3>
                    <span class="difficulty-badge ${wordData.difficulty}">${getDifficultyText(wordData.difficulty)}</span>
                </div>
                <p class="word-hint">💡 ${wordData.hint}</p>
                ${wordData.category ? `<p class="word-category">📁 ${wordData.category}</p>` : ''}
                <button class="btn-delete" onclick="deleteWord('${wordData.word_id}', '${wordData.word}')">🗑️ Eliminar</button>
            `;
            wordsListElement.appendChild(wordItem);
        });
        
    } catch (error) {
        hideLoading();
        showError(error.message);
        wordsListElement.innerHTML = '<p class="info-text" style="color: var(--danger-color);">Error al cargar las palabras</p>';
    }
}

// Agregar nueva palabra
addWordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const word = document.getElementById('word').value.trim().toUpperCase();
    const hint = document.getElementById('hint').value.trim();
    const category = document.getElementById('category').value.trim() || null;
    const difficulty = document.getElementById('difficulty').value;
    
    if (!word || !hint) {
        showError('Por favor completa todos los campos requeridos');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/words`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                word: word,
                hint: hint,
                category: category,
                difficulty: difficulty
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al agregar la palabra');
        }
        
        hideLoading();
        showSuccess(`Palabra "${word}" agregada exitosamente`);
        
        // Limpiar formulario
        addWordForm.reset();
        
        // Recargar lista
        await loadWords();
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
});

// Eliminar palabra
async function deleteWord(wordId, wordText) {
    if (!confirm(`¿Estás seguro de que quieres eliminar la palabra "${wordText}"?`)) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/words/${wordId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar la palabra');
        }
        
        hideLoading();
        showSuccess(`Palabra "${wordText}" eliminada exitosamente`);
        
        // Recargar lista
        await loadWords();
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Obtener texto de dificultad
function getDifficultyText(difficulty) {
    const texts = {
        'easy': 'Fácil',
        'medium': 'Media',
        'hard': 'Difícil'
    };
    return texts[difficulty] || 'Media';
}

// Cargar palabras al inicio
loadWords();
