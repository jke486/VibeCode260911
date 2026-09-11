const COLS = 10;
const ROWS = 20;
const BLOCK_SIZE = 30;
const PREVIEW_BLOCK_SIZE = 24;

const boardCanvas = document.getElementById('board');
const boardCtx = boardCanvas.getContext('2d');
const nextCanvas = document.getElementById('next');
const nextCtx = nextCanvas.getContext('2d');

const scoreEl = document.getElementById('score');
const linesEl = document.getElementById('lines');
const levelEl = document.getElementById('level');
const pauseBtn = document.getElementById('pause-btn');
const startBtn = document.getElementById('start-btn');
const restartBtn = document.getElementById('restart-btn');
const levelSelect = document.getElementById('level-select');

const SHAPES = {
  I: { color: '#38bdf8', matrix: [[1, 1, 1, 1]] },
  O: { color: '#facc15', matrix: [[1, 1], [1, 1]] },
  T: { color: '#c084fc', matrix: [[0, 1, 0], [1, 1, 1]] },
  S: { color: '#22c55e', matrix: [[0, 1, 1], [1, 1, 0]] },
  Z: { color: '#f87171', matrix: [[1, 1, 0], [0, 1, 1]] },
  J: { color: '#60a5fa', matrix: [[1, 0, 0], [1, 1, 1]] },
  L: { color: '#fb923c', matrix: [[0, 0, 1], [1, 1, 1]] },
};

const LINE_SCORES = [0, 100, 300, 500, 800];

const state = {
  board: createBoard(),
  currentPiece: null,
  nextPiece: null,
  score: 0,
  lines: 0,
  level: 1,
  selectedLevel: Number(levelSelect.value),
  dropInterval: 800,
  gameOver: false,
  paused: false,
  running: false,
  animationId: null,
  lastTime: 0,
  dropAccumulator: 0,
};

function createBoard() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(null));
}

function getDropInterval(level) {
  return Math.max(120, 800 - (level - 1) * 60);
}

function cloneMatrix(matrix) {
  return matrix.map((row) => [...row]);
}

function randomType() {
  const types = Object.keys(SHAPES);
  return types[Math.floor(Math.random() * types.length)];
}

function createPiece(type) {
  const matrix = cloneMatrix(SHAPES[type].matrix);
  return {
    type,
    matrix,
    x: Math.floor((COLS - matrix[0].length) / 2),
    y: -1,
    color: SHAPES[type].color,
  };
}

function collides(piece, offsetX = 0, offsetY = 0, matrix = piece.matrix) {
  for (let y = 0; y < matrix.length; y += 1) {
    for (let x = 0; x < matrix[y].length; x += 1) {
      if (!matrix[y][x]) continue;

      const newX = piece.x + x + offsetX;
      const newY = piece.y + y + offsetY;

      if (newX < 0 || newX >= COLS || newY >= ROWS) {
        return true;
      }

      if (newY >= 0 && state.board[newY][newX]) {
        return true;
      }
    }
  }

  return false;
}

function rotateMatrix(matrix) {
  return Array.from({ length: matrix[0].length }, (_, index) =>
    Array.from({ length: matrix.length }, (_, innerIndex) => matrix[matrix.length - 1 - innerIndex][index])
  );
}

function spawnPiece() {
  state.currentPiece = state.nextPiece || createPiece(randomType());
  state.currentPiece.x = Math.floor((COLS - state.currentPiece.matrix[0].length) / 2);
  state.currentPiece.y = -1;

  state.nextPiece = createPiece(randomType());

  if (collides(state.currentPiece)) {
    endGame();
  }
}

function mergePiece() {
  const { currentPiece } = state;

  for (let y = 0; y < currentPiece.matrix.length; y += 1) {
    for (let x = 0; x < currentPiece.matrix[y].length; x += 1) {
      if (!currentPiece.matrix[y][x]) continue;

      const boardY = currentPiece.y + y;
      const boardX = currentPiece.x + x;

      if (boardY >= 0) {
        state.board[boardY][boardX] = currentPiece.color;
      }
    }
  }

  clearLines();
  spawnPiece();
  updateHud();
}

function clearLines() {
  let cleared = 0;

  for (let y = ROWS - 1; y >= 0; y -= 1) {
    if (state.board[y].every((cell) => cell)) {
      state.board.splice(y, 1);
      state.board.unshift(Array(COLS).fill(null));
      cleared += 1;
      y += 1;
    }
  }

  if (cleared > 0) {
    state.lines += cleared;
    state.score += LINE_SCORES[cleared] * state.level;
    state.level = state.selectedLevel + Math.floor(state.lines / 10);
    state.dropInterval = getDropInterval(state.level);
  }
}

function movePiece(dx, dy) {
  const candidate = {
    ...state.currentPiece,
    x: state.currentPiece.x + dx,
    y: state.currentPiece.y + dy,
  };

  if (!collides(candidate)) {
    state.currentPiece = candidate;
    return true;
  }

  return false;
}

function tryRotate() {
  const rotated = rotateMatrix(state.currentPiece.matrix);
  const kicks = [0, -1, 1, -2, 2];

  for (const kick of kicks) {
    const candidate = {
      ...state.currentPiece,
      x: state.currentPiece.x + kick,
      matrix: rotated,
    };

    if (!collides(candidate)) {
      state.currentPiece = candidate;
      return;
    }
  }
}

function hardDrop() {
  if (!state.currentPiece || state.paused || state.gameOver) return;

  let distance = 0;

  while (!collides(state.currentPiece, 0, 1)) {
    state.currentPiece.y += 1;
    distance += 1;
  }

  state.score += distance * 2;
  mergePiece();
  updateHud();
}

function softDrop() {
  if (!state.currentPiece || state.paused || state.gameOver) return;

  if (movePiece(0, 1)) {
    state.score += 1;
  } else {
    mergePiece();
  }

  updateHud();
}

function endGame() {
  state.gameOver = true;
  state.running = false;
  state.paused = false;
  pauseBtn.textContent = '일시정지';
  draw();
}

function updateHud() {
  scoreEl.textContent = state.score;
  linesEl.textContent = state.lines;
  levelEl.textContent = state.level;
}

function drawCell(ctx, x, y, color, size) {
  ctx.fillStyle = color;
  ctx.fillRect(x * size, y * size, size, size);

  ctx.strokeStyle = 'rgba(255,255,255,0.18)';
  ctx.strokeRect(x * size + 0.5, y * size + 0.5, size - 1, size - 1);
}

function drawBoard() {
  boardCtx.clearRect(0, 0, boardCanvas.width, boardCanvas.height);
  boardCtx.fillStyle = '#0b1120';
  boardCtx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);

  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLS; x += 1) {
      const cell = state.board[y][x];
      if (cell) {
        drawCell(boardCtx, x, y, cell, BLOCK_SIZE);
      }
    }
  }

  if (state.currentPiece) {
    state.currentPiece.matrix.forEach((row, y) => {
      row.forEach((value, x) => {
        if (value) {
          const drawY = state.currentPiece.y + y;
          const drawX = state.currentPiece.x + x;

          if (drawY >= 0) {
            drawCell(boardCtx, drawX, drawY, state.currentPiece.color, BLOCK_SIZE);
          }
        }
      });
    });
  }

  if (state.gameOver) {
    boardCtx.fillStyle = 'rgba(2, 6, 23, 0.72)';
    boardCtx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);

    boardCtx.fillStyle = '#f8fafc';
    boardCtx.font = 'bold 28px sans-serif';
    boardCtx.textAlign = 'center';
    boardCtx.fillText('Game Over', boardCanvas.width / 2, boardCanvas.height / 2 - 10);
    boardCtx.font = '18px sans-serif';
    boardCtx.fillText('R키 또는 재시작 버튼', boardCanvas.width / 2, boardCanvas.height / 2 + 24);
  }
}

function drawNextPiece() {
  nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
  nextCtx.fillStyle = '#0b1120';
  nextCtx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);

  if (!state.nextPiece) return;

  const matrix = state.nextPiece.matrix;
  const offsetX = Math.floor((4 - matrix[0].length) / 2);
  const offsetY = Math.floor((4 - matrix.length) / 2);

  matrix.forEach((row, y) => {
    row.forEach((value, x) => {
      if (value) {
        drawCell(nextCtx, offsetX + x, offsetY + y, state.nextPiece.color, PREVIEW_BLOCK_SIZE);
      }
    });
  });
}

function draw() {
  drawBoard();
  drawNextPiece();
}

function gameLoop(timestamp) {
  if (!state.running || state.gameOver) return;

  if (!state.lastTime) {
    state.lastTime = timestamp;
  }

  const delta = timestamp - state.lastTime;
  state.lastTime = timestamp;

  if (!state.paused) {
    state.dropAccumulator += delta;

    while (state.dropAccumulator >= state.dropInterval) {
      if (!movePiece(0, 1)) {
        mergePiece();
      }
      state.dropAccumulator -= state.dropInterval;
    }
  }

  draw();
  state.animationId = requestAnimationFrame(gameLoop);
}

function resetGame() {
  state.selectedLevel = Number(levelSelect.value);
  state.board = createBoard();
  state.score = 0;
  state.lines = 0;
  state.level = state.selectedLevel;
  state.dropInterval = getDropInterval(state.level);
  state.gameOver = false;
  state.paused = false;
  state.running = true;
  state.lastTime = 0;
  state.dropAccumulator = 0;
  pauseBtn.textContent = '일시정지';

  state.nextPiece = createPiece(randomType());
  spawnPiece();
  updateHud();
  draw();

  if (state.animationId) {
    cancelAnimationFrame(state.animationId);
  }

  state.animationId = requestAnimationFrame(gameLoop);
}

function togglePause() {
  if (state.gameOver) return;

  state.paused = !state.paused;
  pauseBtn.textContent = state.paused ? '계속하기' : '일시정지';
  draw();
}

function handleKeyDown(event) {
  if (event.code === 'KeyP') {
    event.preventDefault();
    togglePause();
    return;
  }

  if (event.code === 'KeyR' && state.gameOver) {
    event.preventDefault();
    resetGame();
    return;
  }

  if (state.paused || state.gameOver) return;

  switch (event.code) {
    case 'ArrowLeft':
      event.preventDefault();
      movePiece(-1, 0);
      break;
    case 'ArrowRight':
      event.preventDefault();
      movePiece(1, 0);
      break;
    case 'ArrowDown':
      event.preventDefault();
      softDrop();
      break;
    case 'ArrowUp':
      event.preventDefault();
      tryRotate();
      break;
    case 'Space':
      event.preventDefault();
      hardDrop();
      break;
    default:
      break;
  }

  draw();
}

startBtn.addEventListener('click', () => {
  resetGame();
});

levelSelect.addEventListener('change', () => {
  state.selectedLevel = Number(levelSelect.value);
  state.level = state.selectedLevel;
  state.dropInterval = getDropInterval(state.level);
  updateHud();
});

pauseBtn.addEventListener('click', () => {
  togglePause();
});

restartBtn.addEventListener('click', () => {
  resetGame();
});

document.addEventListener('keydown', handleKeyDown);

updateHud();
draw();
