const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const livesEl = document.getElementById('lives');
const levelEl = document.getElementById('level');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');

const BASE_WIDTH = canvas.width;
const BASE_HEIGHT = canvas.height;

const keys = {};
const stars = [];
const clouds = [];
const particles = [];
const enemies = [];
const bullets = [];
const enemyBullets = [];
const powerups = [];

let player;
let animationId = null;
let lastTimestamp = 0;
let spawnTimer = 0;
let enemyShotTimer = 0;
let powerupTimer = 0;
let backgroundScroll = 0;
let gameState = 'ready';
let score = 0;
let level = 1;
let lives = 3;
let highScore = Number(localStorage.getItem('skyAssaultHighScore') || 0);

function initStars() {
  stars.length = 0;
  for (let i = 0; i < 90; i += 1) {
    stars.push({
      x: Math.random() * BASE_WIDTH,
      y: Math.random() * BASE_HEIGHT,
      size: Math.random() * 2.2 + 0.8,
      speed: Math.random() * 45 + 15,
      alpha: Math.random() * 0.8 + 0.2,
    });
  }
}

function initClouds() {
  clouds.length = 0;
  for (let i = 0; i < 8; i += 1) {
    clouds.push({
      x: Math.random() * BASE_WIDTH,
      y: Math.random() * (BASE_HEIGHT * 0.6),
      width: Math.random() * 110 + 90,
      height: Math.random() * 32 + 18,
      speed: Math.random() * 20 + 12,
    });
  }
}

function resetGame() {
  player = {
    x: BASE_WIDTH / 2,
    y: BASE_HEIGHT - 70,
    width: 32,
    height: 28,
    speed: 360,
    cooldown: 0,
    fireRate: 0.22,
  };

  bullets.length = 0;
  enemyBullets.length = 0;
  enemies.length = 0;
  particles.length = 0;
  powerups.length = 0;

  spawnTimer = 0;
  enemyShotTimer = 0;
  powerupTimer = 3.5;
  backgroundScroll = 0;
  score = 0;
  level = 1;
  lives = 3;

  scoreEl.textContent = String(score);
  livesEl.textContent = String(lives);
  levelEl.textContent = String(level);
}

function setOverlay(message = '') {
  overlay.classList.add('visible');
  overlay.innerHTML = `
    <div class="panel">
      <h1>${message || 'Sky Assault'}</h1>
      <p>좌우 이동: A / D 또는 ← / →</p>
      <p>발사: Space</p>
      <p>목표: 적을 막아 점수를 쌓으세요.</p>
      <button id="startBtn">${gameState === 'over' ? '다시 시작' : '게임 시작'}</button>
    </div>
  `;

  const newBtn = document.getElementById('startBtn');
  newBtn.addEventListener('click', startGame);
}

function startGame() {
  resetGame();
  gameState = 'playing';
  overlay.classList.remove('visible');
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
  lastTimestamp = 0;
  animationId = requestAnimationFrame(loop);
}

function gameOver() {
  gameState = 'over';
  highScore = Math.max(highScore, score);
  localStorage.setItem('skyAssaultHighScore', String(highScore));
  setOverlay(`Game Over\n점수: ${score}`);
  cancelAnimationFrame(animationId);
}

function spawnEnemy() {
  const typeRoll = Math.random();
  const width = typeRoll > 0.7 ? 36 : 28;
  const height = typeRoll > 0.7 ? 28 : 22;
  const fruitPool = ['apple', 'orange', 'lemon', 'berry', 'melon'];
  const fruit = fruitPool[Math.floor(Math.random() * fruitPool.length)];

  enemies.push({
    x: Math.random() * (BASE_WIDTH - 80) + 40,
    y: -40,
    width,
    height,
    speed: 70 + level * 8 + Math.random() * 18,
    type: typeRoll > 0.7 ? 'heavy' : 'scout',
    fruit,
    drift: (Math.random() - 0.5) * 80,
    shootCooldown: Math.random() * 1.8 + 0.8,
  });
}

function shootBullet() {
  bullets.push({
    x: player.x,
    y: player.y - 20,
    width: 4,
    height: 16,
    speed: 520,
  });
}

function shootEnemyBullet(enemy) {
  enemyBullets.push({
    x: enemy.x,
    y: enemy.y + enemy.height / 2,
    width: 4,
    height: 16,
    speed: 240 + level * 20,
  });
}

function spawnPowerup() {
  const types = ['rapid', 'shield', 'heal'];
  const type = types[Math.floor(Math.random() * types.length)];

  powerups.push({
    x: Math.random() * (BASE_WIDTH - 80) + 40,
    y: -20,
    width: 22,
    height: 22,
    type,
    bob: Math.random() * Math.PI * 2,
  });
}

function createParticles(x, y, color, count = 14) {
  for (let i = 0; i < count; i += 1) {
    particles.push({
      x,
      y,
      vx: (Math.random() - 0.5) * 150,
      vy: Math.random() * -120 - 20,
      size: Math.random() * 4 + 2,
      color,
      life: Math.random() * 0.5 + 0.4,
    });
  }
}

function updatePlayer(dt) {
  if (keys['ArrowLeft'] || keys['a']) {
    player.x -= player.speed * dt;
  }
  if (keys['ArrowRight'] || keys['d']) {
    player.x += player.speed * dt;
  }

  player.x = Math.max(player.width / 2, Math.min(BASE_WIDTH - player.width / 2, player.x));

  player.rapidTimer = Math.max(0, (player.rapidTimer || 0) - dt);
  player.shieldTimer = Math.max(0, (player.shieldTimer || 0) - dt);

  const fireRate = player.rapidTimer > 0 ? 0.08 : player.fireRate;

  if ((keys[' '] || keys['Space']) && player.cooldown <= 0) {
    shootBullet();
    player.cooldown = fireRate;
  }

  player.cooldown = Math.max(0, player.cooldown - dt);
}

function updateBullets(dt) {
  for (let i = bullets.length - 1; i >= 0; i -= 1) {
    const bullet = bullets[i];
    bullet.y -= bullet.speed * dt;

    if (bullet.y < -20) {
      bullets.splice(i, 1);
    }
  }

  for (let i = enemyBullets.length - 1; i >= 0; i -= 1) {
    const bullet = enemyBullets[i];
    bullet.y += bullet.speed * dt;

    if (bullet.y > BASE_HEIGHT + 20) {
      enemyBullets.splice(i, 1);
    }
  }
}

function updateEnemies(dt) {
  spawnTimer -= dt;
  if (spawnTimer <= 0) {
    spawnEnemy();
    spawnTimer = Math.max(0.45, 1 - level * 0.05) * (Math.random() * 0.6 + 0.8);
  }

  for (let i = enemies.length - 1; i >= 0; i -= 1) {
    const enemy = enemies[i];
    enemy.x += enemy.drift * dt;
    enemy.y += enemy.speed * dt;
    enemy.shootCooldown -= dt;

    if (enemy.x < 20 || enemy.x > BASE_WIDTH - 20) {
      enemy.drift *= -1;
      enemy.x = Math.max(20, Math.min(BASE_WIDTH - 20, enemy.x));
    }

    if (enemy.shootCooldown <= 0 && enemy.y > 80) {
      shootEnemyBullet(enemy);
      enemy.shootCooldown = Math.random() * 1.5 + 1.2;
    }

    if (enemy.y > BASE_HEIGHT + 60) {
      enemies.splice(i, 1);
      loseLife();
      continue;
    }

    for (let j = bullets.length - 1; j >= 0; j -= 1) {
      const bullet = bullets[j];
      if (rectIntersect(enemy, bullet)) {
        enemies.splice(i, 1);
        bullets.splice(j, 1);

        score += enemy.type === 'heavy' ? 20 : 10;
        createParticles(enemy.x, enemy.y, enemy.type === 'heavy' ? '#ffae63' : '#8ef6cf', enemy.type === 'heavy' ? 20 : 14);
        break;
      }
    }
  }
}

function applyPowerup(powerup) {
  if (powerup.type === 'rapid') {
    player.rapidTimer = 5;
    createParticles(powerup.x, powerup.y, '#ffde59', 18);
  } else if (powerup.type === 'shield') {
    player.shieldTimer = 6;
    createParticles(powerup.x, powerup.y, '#8ef6cf', 20);
  } else if (powerup.type === 'heal') {
    lives = Math.min(lives + 1, 5);
    livesEl.textContent = String(lives);
    createParticles(powerup.x, powerup.y, '#ff9ebe', 20);
  }
}

function updatePowerups(dt) {
  powerupTimer -= dt;
  if (powerupTimer <= 0) {
    spawnPowerup();
    powerupTimer = 7 + Math.random() * 4;
  }

  for (let i = powerups.length - 1; i >= 0; i -= 1) {
    const powerup = powerups[i];
    powerup.y += 90 * dt;
    powerup.bob += dt * 5;

    if (powerup.y > BASE_HEIGHT + 30) {
      powerups.splice(i, 1);
      continue;
    }

    if (rectIntersect(player, powerup)) {
      applyPowerup(powerup);
      powerups.splice(i, 1);
    }
  }
}

function loseLife() {
  if (player.shieldTimer > 0) {
    return;
  }

  lives -= 1;
  livesEl.textContent = String(lives);
  createParticles(player.x, player.y, '#ff6b6b', 30);

  if (lives <= 0) {
    gameOver();
  }
}

function updateParticles(dt) {
  for (let i = particles.length - 1; i >= 0; i -= 1) {
    const p = particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.life -= dt;

    if (p.life <= 0) {
      particles.splice(i, 1);
    }
  }
}

function updateGame(dt) {
  backgroundScroll += dt * 90;
  level = Math.floor(score / 120) + 1;
  levelEl.textContent = String(level);

  updatePlayer(dt);
  updateBullets(dt);
  updateEnemies(dt);
  updatePowerups(dt);
  updateParticles(dt);
  updateEnemyHits();

  if (score > highScore) {
    highScore = score;
  }
}

function updateEnemyHits() {
  for (let i = enemyBullets.length - 1; i >= 0; i -= 1) {
    const bullet = enemyBullets[i];
    if (rectIntersect(player, bullet)) {
      enemyBullets.splice(i, 1);

      if (player.shieldTimer > 0) {
        createParticles(player.x, player.y, '#8ef6cf', 14);
        continue;
      }

      loseLife();
    }
  }
}

function rectIntersect(a, b) {
  return (
    a.x - a.width / 2 < b.x + b.width / 2 &&
    a.x + a.width / 2 > b.x - b.width / 2 &&
    a.y - a.height / 2 < b.y + b.height / 2 &&
    a.y + a.height / 2 > b.y - b.height / 2
  );
}

function drawBackground() {
  ctx.fillStyle = '#061722';
  ctx.fillRect(0, 0, BASE_WIDTH, BASE_HEIGHT);

  for (const star of stars) {
    star.y += star.speed * (1 / 60);
    if (star.y > BASE_HEIGHT) {
      star.y = -10;
      star.x = Math.random() * BASE_WIDTH;
    }

    ctx.fillStyle = `rgba(255,255,255,${star.alpha})`;
    ctx.fillRect(star.x, star.y, star.size, star.size);
  }

  for (const cloud of clouds) {
    cloud.x -= cloud.speed * (1 / 60);
    if (cloud.x < -cloud.width) {
      cloud.x = BASE_WIDTH + cloud.width;
      cloud.y = Math.random() * (BASE_HEIGHT * 0.5);
    }

    ctx.fillStyle = 'rgba(160, 220, 255, 0.18)';
    ctx.beginPath();
    ctx.ellipse(cloud.x, cloud.y, cloud.width * 0.36, cloud.height * 0.7, 0, 0, Math.PI * 2);
    ctx.ellipse(cloud.x + cloud.width * 0.18, cloud.y - 8, cloud.width * 0.28, cloud.height * 0.58, 0, 0, Math.PI * 2);
    ctx.ellipse(cloud.x - cloud.width * 0.2, cloud.y - 6, cloud.width * 0.24, cloud.height * 0.52, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = '#0d2532';
  ctx.fillRect(0, BASE_HEIGHT - 54, BASE_WIDTH, 54);

  ctx.fillStyle = '#17394a';
  for (let x = 0; x < BASE_WIDTH; x += 36) {
    ctx.fillRect(x + ((backgroundScroll * 0.5) % 36), BASE_HEIGHT - 54, 20, 20);
  }
}

function drawPlayer() {
  ctx.save();
  ctx.translate(player.x, player.y);

  ctx.shadowColor = 'rgba(110, 231, 255, 0.8)';
  ctx.shadowBlur = 18;

  ctx.fillStyle = '#7ef9ff';

  ctx.beginPath();
  ctx.moveTo(0, -22);
  ctx.lineTo(18, -4);
  ctx.lineTo(36, 0);
  ctx.lineTo(18, 14);
  ctx.lineTo(0, 20);
  ctx.lineTo(-18, 14);
  ctx.lineTo(-36, 0);
  ctx.lineTo(-18, -4);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#b58bff';
  ctx.fillRect(-5, 6, 10, 16);

  ctx.fillStyle = '#0f2237';
  ctx.beginPath();
  ctx.moveTo(-8, -6);
  ctx.lineTo(8, -6);
  ctx.lineTo(12, 8);
  ctx.lineTo(-12, 8);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = '#dffaff';
  ctx.beginPath();
  ctx.arc(0, -2, 6, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#ffcb6b';
  ctx.fillRect(-38, -2, 14, 4);
  ctx.fillRect(24, -2, 14, 4);

  ctx.fillStyle = '#5ad0ff';
  ctx.fillRect(-4, 22, 8, 10);

  ctx.restore();
}

function drawBullets() {
  ctx.fillStyle = '#ffe39a';
  for (const bullet of bullets) {
    ctx.fillRect(bullet.x - bullet.width / 2, bullet.y - bullet.height / 2, bullet.width, bullet.height);
  }

  ctx.fillStyle = '#ff8b8b';
  for (const bullet of enemyBullets) {
    ctx.fillRect(bullet.x - bullet.width / 2, bullet.y - bullet.height / 2, bullet.width, bullet.height);
  }
}

function drawPowerups() {
  for (const powerup of powerups) {
    const bobOffset = Math.sin(powerup.bob) * 4;
    const cx = powerup.x;
    const cy = powerup.y + bobOffset;

    ctx.save();
    ctx.translate(cx, cy);

    if (powerup.type === 'rapid') {
      ctx.fillStyle = '#ffd166';
      ctx.beginPath();
      ctx.arc(0, 0, powerup.width / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fff6cf';
      ctx.fillRect(-2, -8, 4, 16);
      ctx.fillRect(-8, -2, 16, 4);
    } else if (powerup.type === 'shield') {
      ctx.strokeStyle = '#7ef9ff';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(0, 0, powerup.width / 2, 0, Math.PI * 2);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-5, -5);
      ctx.lineTo(5, 5);
      ctx.moveTo(5, -5);
      ctx.lineTo(-5, 5);
      ctx.stroke();
    } else {
      ctx.fillStyle = '#ff7aa2';
      ctx.beginPath();
      ctx.arc(0, 0, powerup.width / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillRect(-2, -8, 4, 16);
    }

    ctx.restore();
  }
}

function drawEnemies() {
  for (const enemy of enemies) {
    ctx.save();
    ctx.translate(enemy.x, enemy.y);

    const fruitColors = {
      apple: '#ef4f60',
      orange: '#ff9f43',
      lemon: '#f6d55c',
      berry: '#b454e3',
      melon: '#4dd29d',
    };

    const color = fruitColors[enemy.fruit] || '#ff9f43';

    ctx.shadowColor = 'rgba(0, 0, 0, 0.18)';
    ctx.shadowBlur = 10;

    if (enemy.fruit === 'apple') {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(0, 0, enemy.width / 2, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#2f8f57';
      ctx.beginPath();
      ctx.moveTo(-2, -enemy.height * 0.18);
      ctx.quadraticCurveTo(8, -enemy.height * 0.45, 10, -enemy.height * 0.75);
      ctx.quadraticCurveTo(2, -enemy.height * 0.4, -2, -enemy.height * 0.18);
      ctx.fill();

      ctx.fillStyle = '#6a3d1c';
      ctx.fillRect(7, -enemy.height * 0.76, 2, 8);
    } else if (enemy.fruit === 'orange') {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.ellipse(0, 0, enemy.width / 2, enemy.height / 2, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = 'rgba(255,255,255,0.5)';
      ctx.lineWidth = 2;
      for (let i = -1; i <= 1; i += 1) {
        ctx.beginPath();
        ctx.moveTo(i * 4, -enemy.height / 2 + 4);
        ctx.lineTo(i * 4, enemy.height / 2 - 4);
        ctx.stroke();
      }

      ctx.fillStyle = '#2f8f57';
      ctx.beginPath();
      ctx.moveTo(-4, -enemy.height * 0.2);
      ctx.quadraticCurveTo(5, -enemy.height * 0.5, 8, -enemy.height * 0.7);
      ctx.quadraticCurveTo(1, -enemy.height * 0.35, -4, -enemy.height * 0.2);
      ctx.fill();
    } else if (enemy.fruit === 'lemon') {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.ellipse(0, 0, enemy.width / 2, enemy.height / 2, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#2f8f57';
      ctx.beginPath();
      ctx.moveTo(-4, -enemy.height * 0.3);
      ctx.quadraticCurveTo(6, -enemy.height * 0.6, 9, -enemy.height * 0.8);
      ctx.quadraticCurveTo(0, -enemy.height * 0.35, -4, -enemy.height * 0.3);
      ctx.fill();
    } else if (enemy.fruit === 'berry') {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(-enemy.width * 0.16, 0, enemy.width * 0.26, 0, Math.PI * 2);
      ctx.arc(enemy.width * 0.16, 0, enemy.width * 0.26, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#f5e7ff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, -enemy.height * 0.12);
      ctx.lineTo(0, enemy.height * 0.12);
      ctx.stroke();

      ctx.fillStyle = '#2f8f57';
      ctx.beginPath();
      ctx.moveTo(-4, -enemy.height * 0.15);
      ctx.quadraticCurveTo(2, -enemy.height * 0.48, 6, -enemy.height * 0.7);
      ctx.quadraticCurveTo(-1, -enemy.height * 0.35, -4, -enemy.height * 0.15);
      ctx.fill();
    } else {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.ellipse(0, 0, enemy.width / 2, enemy.height / 2, 0, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = 'rgba(255,255,255,0.4)';
      ctx.lineWidth = 2;
      for (let i = -2; i <= 2; i += 1) {
        ctx.beginPath();
        ctx.moveTo(i * 4, -enemy.height / 2);
        ctx.lineTo(i * 4, enemy.height / 2);
        ctx.stroke();
      }

      ctx.fillStyle = '#2f8f57';
      ctx.beginPath();
      ctx.moveTo(-5, -enemy.height * 0.18);
      ctx.quadraticCurveTo(7, -enemy.height * 0.7, 10, -enemy.height * 0.9);
      ctx.quadraticCurveTo(1, -enemy.height * 0.38, -5, -enemy.height * 0.18);
      ctx.fill();
    }

    ctx.restore();
  }
}

function drawParticles() {
  for (const p of particles) {
    ctx.globalAlpha = Math.max(0, p.life);
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, p.size, p.size);
  }
  ctx.globalAlpha = 1;
}

function drawScoreText() {
  ctx.fillStyle = 'rgba(255,255,255,0.8)';
  ctx.font = '18px Arial';
  ctx.fillText(`High Score: ${highScore}`, 20, 30);
}

function loop(timestamp) {
  if (gameState !== 'playing') return;

  if (!lastTimestamp) {
    lastTimestamp = timestamp;
  }

  const dt = Math.min((timestamp - lastTimestamp) / 1000, 0.033);
  lastTimestamp = timestamp;

  updateGame(dt);
  render();

  animationId = requestAnimationFrame(loop);
}

function render() {
  drawBackground();
  drawPlayer();
  drawBullets();
  drawPowerups();
  drawEnemies();
  drawParticles();
  drawScoreText();
  scoreEl.textContent = String(score);
}

startBtn.addEventListener('click', startGame);

window.addEventListener('keydown', (event) => {
  const key = event.key;
  if (['ArrowLeft', 'ArrowRight', ' ', 'Space', 'a', 'A', 'd', 'D'].includes(key)) {
    event.preventDefault();
  }

  keys[key] = true;
  keys[key.toLowerCase()] = true;
});

window.addEventListener('keyup', (event) => {
  const key = event.key;
  keys[key] = false;
  keys[key.toLowerCase()] = false;
});

initStars();
initClouds();
setOverlay();
render();
