'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const CLI = path.join(__dirname, '..', 'cli.js');

function pastaTemp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'loja-cli-'));
}

function rodar(db, ...args) {
  return execFileSync(process.execPath, [CLI, '--db', db, ...args], { encoding: 'utf8' });
}

test('cli: cadastra e lista clientes', () => {
  const pasta = pastaTemp();
  const db = path.join(pasta, 'loja.db');
  try {
    assert.strictEqual(rodar(db, 'init'), 'Banco pronto.\n');
    assert.strictEqual(rodar(db, 'cliente:novo', 'Ana Souza', '52998224725', 'ana@exemplo.com'), 'Cliente #1 cadastrado: Ana Souza\n');
    assert.strictEqual(rodar(db, 'clientes'), '#1 | Ana Souza | 529.982.247-25 | ana@exemplo.com | -\n');
  } finally {
    fs.rmSync(pasta, { recursive: true, force: true });
  }
});

test('cli: produto e pedido', () => {
  const pasta = pastaTemp();
  const db = path.join(pasta, 'loja.db');
  try {
    rodar(db, 'usuario:novo', 'carlos', 'Carlos', 'balcao', 'vendedor');
    rodar(db, 'cliente:novo', 'Ana Souza', '52998224725');
    assert.strictEqual(rodar(db, 'produto:novo', 'arroz5', 'Arroz 5kg', '25,00', '50'), 'Produto #1 cadastrado: ARROZ5 Arroz 5kg R$ 25,00\n');
    assert.strictEqual(
      rodar(db, 'pedido:novo', '1', '1', '1:4'),
      'Pedido #1 criado. Subtotal: R$ 100,00 | Desconto: R$ 0,00 | Total: R$ 100,00\n'
    );
    assert.strictEqual(rodar(db, 'produtos'), '#1 | ARROZ5 | Arroz 5kg | R$ 25,00 | estoque 46\n');
  } finally {
    fs.rmSync(pasta, { recursive: true, force: true });
  }
});

test('cli: erro vai para stderr com codigo 1', () => {
  const pasta = pastaTemp();
  const db = path.join(pasta, 'loja.db');
  try {
    assert.throws(() => execFileSync(process.execPath, [CLI, '--db', db, 'comando-que-nao-existe'], { stdio: 'pipe' }),
      (e) => e.status === 1);
  } finally {
    fs.rmSync(pasta, { recursive: true, force: true });
  }
});
