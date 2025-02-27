const emojis = ['😊', '😌', '🥰', '😎', '🌸', '💪', '🧘‍♀️', '✨'];
const gridSize = 8;
let score = 0;
let moves = 0;
let gameBoard = [];
let selectedBlock = null;

function generateBoard() {
    gameBoard = [];
    for (let row = 0; row < gridSize; row++) {
        let rowArray = [];
        for (let col = 0; col < gridSize; col++) {
            rowArray.push({
                emoji: emojis[Math.floor(Math.random() * emojis.length)],
                isMatched: false
            });
        }
        gameBoard.push(rowArray);
    }
    while (findMatches().length > 0) {
        removeMatches();
        fillBoard();
    }
    renderBoard();
}

function renderBoard() {
    const container = document.getElementById('game-container');
    container.innerHTML = '';
    for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize; col++) {
            const block = gameBoard[row][col];
            const div = document.createElement('div');
            div.classList.add('block');
            div.setAttribute('data-row', row);
            div.setAttribute('data-col', col);
            div.innerText = block.emoji;
            div.addEventListener('click', () => blockClicked(row, col));
            container.appendChild(div);
        }
    }
}

async function blockClicked(row, col) {
    const block = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
    
    if (!selectedBlock) {
        selectedBlock = { row, col, element: block };
        block.classList.add('selected');
        return;
    }

    if (selectedBlock.row === row && selectedBlock.col === col) {
        selectedBlock.element.classList.remove('selected');
        selectedBlock = null;
        return;
    }

    if (isAdjacent(selectedBlock.row, selectedBlock.col, row, col)) {
        swapBlocks(selectedBlock.row, selectedBlock.col, row, col);
        selectedBlock.element.classList.remove('selected');
        moves++;
        document.getElementById('moves').innerText = `Moves: ${moves}`;
        
        if (findMatches().length === 0) {
            // Swap back if no matches
            swapBlocks(row, col, selectedBlock.row, selectedBlock.col);
        } else {
            while (true) {
                const matches = findMatches();
                if (matches.length === 0) break;
                
                removeMatches();
                updateScore(matches.length);
                fillBoard();
                await new Promise(resolve => setTimeout(resolve, 300));
                renderBoard();
            }
        }
    }
    
    selectedBlock = null;
}

function isAdjacent(row1, col1, row2, col2) {
    return (Math.abs(row1 - row2) === 1 && col1 === col2) ||
           (Math.abs(col1 - col2) === 1 && row1 === row2);
}

function swapBlocks(row1, col1, row2, col2) {
    const temp = gameBoard[row1][col1];
    gameBoard[row1][col1] = gameBoard[row2][col2];
    gameBoard[row2][col2] = temp;
    renderBoard();
}

function findMatches() {
    const matches = [];
    
    // Check horizontal matches
    for (let row = 0; row < gridSize; row++) {
        for (let col = 0; col < gridSize - 2; col++) {
            const emoji = gameBoard[row][col].emoji;
            if (emoji === gameBoard[row][col + 1].emoji &&
                emoji === gameBoard[row][col + 2].emoji) {
                matches.push({ row, col });
                matches.push({ row, col: col + 1 });
                matches.push({ row, col: col + 2 });
            }
        }
    }
    
    // Check vertical matches
    for (let row = 0; row < gridSize - 2; row++) {
        for (let col = 0; col < gridSize; col++) {
            const emoji = gameBoard[row][col].emoji;
            if (emoji === gameBoard[row + 1][col].emoji &&
                emoji === gameBoard[row + 2][col].emoji) {
                matches.push({ row, col });
                matches.push({ row: row + 1, col });
                matches.push({ row: row + 2, col });
            }
        }
    }
    
    return [...new Set(matches.map(m => JSON.stringify(m)))].map(m => JSON.parse(m));
}

function removeMatches() {
    const matches = findMatches();
    matches.forEach(match => {
        const block = document.querySelector(`[data-row="${match.row}"][data-col="${match.col}"]`);
        if (block) {
            block.classList.add('matched');
        }
        gameBoard[match.row][match.col] = null;
    });
}

function fillBoard() {
    // Move existing blocks down
    for (let col = 0; col < gridSize; col++) {
        let emptySpaces = 0;
        for (let row = gridSize - 1; row >= 0; row--) {
            if (!gameBoard[row][col]) {
                emptySpaces++;
            } else if (emptySpaces > 0) {
                gameBoard[row + emptySpaces][col] = gameBoard[row][col];
                gameBoard[row][col] = null;
            }
        }
    }
    
    // Fill empty spaces with new blocks
    for (let col = 0; col < gridSize; col++) {
        for (let row = 0; row < gridSize; row++) {
            if (!gameBoard[row][col]) {
                gameBoard[row][col] = {
                    emoji: emojis[Math.floor(Math.random() * emojis.length)],
                    isMatched: false
                };
            }
        }
    }
}

function updateScore(matchCount) {
    score += matchCount * 10;
    document.getElementById('score').innerText = `Score: ${score}`;
}

function resetGame() {
    score = 0;
    moves = 0;
    selectedBlock = null;
    document.getElementById('score').innerText = 'Score: 0';
    document.getElementById('moves').innerText = 'Moves: 0';
    generateBoard();
}

// Initialize the game
window.addEventListener('load', () => {
    generateBoard();
});
