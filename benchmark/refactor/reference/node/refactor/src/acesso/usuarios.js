'use strict';

// Usuarios do sistema (funcionarios da loja).
// Papeis: 'admin' (dono/gerente) e 'vendedor'.

const crypto = require('node:crypto');
const { agora, linha, linhas } = require('../infra/banco');
const { validarEmail, normalizarLogin, exigirSenhaNova, exigir } = require('../comum/validacao');

const PAPEIS = ['admin', 'vendedor'];
const CAMPOS_PUBLICOS = 'id, login, nome, email, papel, ativo, criado_em';

function hashSenha(senha) {
  return crypto.createHash('md5').update(String(senha)).digest('hex');
}

function conferirSenha(senha, hash) {
  return hashSenha(senha) === hash;
}

/**
 * Cria um usuario.
 * @param {DatabaseSync} db
 * @param {{login:string, nome:string, senha:string, papel:string, email?:string}} dados
 * @returns {object} usuario sem a senha
 */
function criarUsuario(db, dados) {
  exigir(dados, 'Dados do usuario nao informados');
  const login = normalizarLogin(dados.login);
  exigir(dados.nome && String(dados.nome).trim().length >= 2, 'Nome do usuario obrigatorio');
  exigirSenhaNova(dados.senha);
  const papel = dados.papel || 'vendedor';
  exigir(PAPEIS.includes(papel), 'Papel invalido: ' + papel);
  exigir(!dados.email || validarEmail(dados.email), 'E-mail invalido');
  exigir(!db.prepare('SELECT id FROM usuarios WHERE login = ?').get(login), 'Login ja existe: ' + login);
  const r = db.prepare(
    'INSERT INTO usuarios (login, nome, email, senha_hash, papel, ativo, criado_em) VALUES (?, ?, ?, ?, ?, 1, ?)'
  ).run(login, String(dados.nome).trim(), dados.email ? String(dados.email).trim().toLowerCase() : null,
    hashSenha(dados.senha), papel, agora());
  return buscarUsuario(db, Number(r.lastInsertRowid));
}

function buscarUsuario(db, id) {
  return linha(db.prepare('SELECT ' + CAMPOS_PUBLICOS + ' FROM usuarios WHERE id = ?').get(Number(id)));
}

// inclui o hash; uso interno da autenticacao
function buscarCredenciais(db, login) {
  return linha(db.prepare('SELECT id, login, senha_hash, papel, ativo FROM usuarios WHERE login = ?')
    .get(String(login || '').trim().toLowerCase()));
}

/**
 * Lista usuarios por login.
 */
function listarUsuarios(db) {
  return linhas(db.prepare('SELECT ' + CAMPOS_PUBLICOS + ' FROM usuarios ORDER BY login').all());
}

/**
 * Troca a senha conferindo a atual.
 */
function alterarSenha(db, usuarioId, senhaAtual, senhaNova) {
  const u = db.prepare('SELECT id, senha_hash FROM usuarios WHERE id = ?').get(Number(usuarioId));
  if (!u) throw new Error('Usuario nao encontrado');
  if (!conferirSenha(senhaAtual, u.senha_hash)) {
    throw new Error('Senha atual nao confere');
  }
  exigirSenhaNova(senhaNova);
  db.prepare('UPDATE usuarios SET senha_hash = ? WHERE id = ?').run(hashSenha(senhaNova), u.id);
  // derruba as sessoes abertas
  db.prepare('DELETE FROM sessoes WHERE usuario_id = ?').run(u.id);
  return true;
}

/**
 * Senha nova definida pelo administrador (quando o funcionario esquece).
 */
function redefinirSenha(db, usuarioId, senhaNova) {
  const u = buscarUsuario(db, usuarioId);
  if (!u) throw new Error('Usuario nao encontrado');
  exigirSenhaNova(senhaNova);
  db.prepare('UPDATE usuarios SET senha_hash = ? WHERE id = ?').run(hashSenha(senhaNova), u.id);
  db.prepare('DELETE FROM sessoes WHERE usuario_id = ?').run(u.id);
  return true;
}

/**
 * Desativa o usuario (nao apaga, por causa dos pedidos lancados por ele).
 */
function desativarUsuario(db, usuarioId) {
  const u = buscarUsuario(db, usuarioId);
  if (!u) throw new Error('Usuario nao encontrado');
  db.prepare('UPDATE usuarios SET ativo = 0 WHERE id = ?').run(u.id);
  db.prepare('DELETE FROM sessoes WHERE usuario_id = ?').run(u.id);
  return true;
}

module.exports = {
  criarUsuario,
  buscarUsuario,
  buscarCredenciais,
  listarUsuarios,
  alterarSenha,
  redefinirSenha,
  desativarUsuario,
  hashSenha,
  conferirSenha,
  PAPEIS,
};
