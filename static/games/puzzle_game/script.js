class PuzzleGame {
    constructor() {
        this.container = document.getElementById('puzzle-container');
        this.previewImage = document.getElementById('preview-image');
        this.moves = 0;
        this.timer = 0;
        this.timerInterval = null;
        this.size = 3;
        this.tiles = [];
        this.emptyTile = null;
        this.selectedTile = null;
        
        // Initialize controls
        document.getElementById('start-btn').addEventListener('click', () => this.startNewGame());
        document.getElementById('difficulty').addEventListener('change', (e) => {
            this.size = parseInt(e.target.value);
            this.startNewGame();
        });
        
        this.startNewGame();
    }
    
    startNewGame() {
        // Clear previous game
        clearInterval(this.timerInterval);
        this.moves = 0;
        this.timer = 0;
        this.selectedTile = null;
        this.updateStats();
        
        // Create puzzle grid
        this.container.style.gridTemplateColumns = `repeat(${this.size}, 100px)`;
        this.container.innerHTML = '';
        
        // Create tiles
        this.tiles = [];
        for (let i = 0; i < this.size * this.size; i++) {
            const tile = this.createTile(i);
            this.tiles.push(tile);
            this.container.appendChild(tile);
        }
        
        // Shuffle tiles
        this.shuffleTiles();
        
        // Start timer
        this.startTimer();
    }
    
    createTile(index) {
        const tile = document.createElement('div');
        tile.className = 'puzzle-piece';
        tile.dataset.index = index;
        
        const row = Math.floor(index / this.size);
        const col = index % this.size;
        const bgPosX = (col * 100) / (this.size - 1);
        const bgPosY = (row * 100) / (this.size - 1);
        
        tile.style.backgroundImage = `url(${this.previewImage.src})`;
        tile.style.backgroundSize = `${this.size * 100}%`;
        tile.style.backgroundPosition = `${bgPosX}% ${bgPosY}%`;
        
        tile.addEventListener('click', () => this.tileClicked(tile));
        
        return tile;
    }
    
    shuffleTiles() {
        for (let i = this.tiles.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            this.swapTiles(this.tiles[i], this.tiles[j]);
        }
        
        // Ensure puzzle is solvable
        if (!this.isSolvable()) {
            // Swap last two tiles if puzzle is not solvable
            this.swapTiles(this.tiles[this.tiles.length - 1], this.tiles[this.tiles.length - 2]);
        }
    }
    
    isSolvable() {
        let inversions = 0;
        for (let i = 0; i < this.tiles.length - 1; i++) {
            for (let j = i + 1; j < this.tiles.length; j++) {
                if (parseInt(this.tiles[i].dataset.index) > parseInt(this.tiles[j].dataset.index)) {
                    inversions++;
                }
            }
        }
        return inversions % 2 === 0;
    }
    
    tileClicked(tile) {
        if (!this.selectedTile) {
            this.selectedTile = tile;
            tile.classList.add('selected');
        } else {
            if (tile === this.selectedTile) {
                tile.classList.remove('selected');
                this.selectedTile = null;
            } else {
                this.swapTiles(this.selectedTile, tile);
                this.selectedTile.classList.remove('selected');
                this.selectedTile = null;
                this.moves++;
                this.updateStats();
                
                if (this.checkWin()) {
                    clearInterval(this.timerInterval);
                    this.container.classList.add('completed');
                    setTimeout(() => {
                        alert(`Congratulations! You solved the puzzle in ${this.moves} moves and ${this.formatTime(this.timer)}!`);
                        this.container.classList.remove('completed');
                    }, 1000);
                }
            }
        }
    }
    
    swapTiles(tile1, tile2) {
        const parent = tile1.parentNode;
        const sibling = tile1.nextSibling === tile2 ? tile1 : tile2.nextSibling;
        parent.insertBefore(tile2, tile1);
        parent.insertBefore(tile1, sibling);
        
        // Update tiles array
        const index1 = this.tiles.indexOf(tile1);
        const index2 = this.tiles.indexOf(tile2);
        [this.tiles[index1], this.tiles[index2]] = [this.tiles[index2], this.tiles[index1]];
    }
    
    checkWin() {
        return this.tiles.every((tile, index) => {
            return parseInt(tile.dataset.index) === index;
        });
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            this.timer++;
            this.updateStats();
        }, 1000);
    }
    
    updateStats() {
        document.getElementById('moves').textContent = `Moves: ${this.moves}`;
        document.getElementById('timer').textContent = `Time: ${this.formatTime(this.timer)}`;
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
        const secs = (seconds % 60).toString().padStart(2, '0');
        return `${mins}:${secs}`;
    }
}

// Start the game when the page loads
window.addEventListener('load', () => {
    new PuzzleGame();
});
