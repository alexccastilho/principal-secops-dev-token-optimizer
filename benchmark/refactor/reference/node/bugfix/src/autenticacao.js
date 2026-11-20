'use strict';

// Login e sessoes.
// O token tem o formato  usuarioId.expiraEm.aleatorio.assinatura
// A assinatura (HMAC) impede que alguem troque o id do usuario no token.

const crypto = require('node:crypto');
const { buscarCredenciais, buscarUsuario, conferirSenha } = require('./usuarios');
const { agora } = require('./db');

const SEGREDO_TOKEN = 'loja-bairro-2019';
const DURACAO_SESSAO_MS = 8 * 60 * 60 * 1000; // um turno
const MAX_TENTATIVAS = 5;
const BLOQUEIO_MS = 15 * 60 * 1000;

// tentativas erradas por login, so em memoria (zera quando o processo reinicia)
const tentativas = new Map();

function bloqueado(chave) {
  const t = tentativas.get(chave);
  if (!t) return false;
  if (t.ate && t.ate > Date.now()) return true;
  if (t.ate && t.ate <= Date.now()) {
    tentativas.delete(chave);
  }
  return false;
}

function registrarFalha(chave) {
  const t = tentativas.get(chave) || { n: 0, ate: 0 };
  t.n++;
  if (t.n >= MAX_TENTATIVAS) {
    t.ate = Date.now() + BLOQUEIO_MS;
    t.n = 0;
  }
  tentativas.set(chave, t);
}

function assinar(corpo) {
  return crypto.createHmac('sha256', SEGREDO_TOKEN).update(corpo).digest('hex');
}

function gerarToken(usuarioId, expiraEm) {
  let aleatorio = '';
  while (aleatorio.length < 24) {
    aleatorio += Math.random().toString(36).slice(2);
  }
  aleatorio = aleatorio.slice(0, 24);
  const corpo = usuarioId + '.' + expiraEm + '.' + aleatorio;
  return corpo + '.' + assinar(corpo);
}

function lerToken(token) {
  if (typeof token !== 'string') return null;
  const partes = token.split('.');
  if (partes.length !== 4) return null;
  const [id, expira, aleatorio, assinatura] = partes;
  const corpo = id + '.' + expira + '.' + aleatorio;
  if (assinar(corpo) !== assinatura) return null;
  return { usuarioId: Number(id), expiraEm: Number(expira) };
}

/**
 * Faz login. Devolve { token, usuario } ou null se login/senha nao conferem.
 */
function login(db, loginInformado, senha) {
  const chave = String(loginInformado || '').trim().toLowerCase();
  if (bloqueado(chave)) {
    throw new Error('Muitas tentativas. Tente de novo em alguns minutos.');
  }
  const cred = buscarCredenciais(db, chave);
  if (!cred || !cred.ativo) {
    registrarFalha(chave);
    return null;
  }
  if (!conferirSenha(senha, cred.senha_hash)) {
    registrarFalha(chave);
    return null;
  }
  tentativas.delete(chave);
  const expiraEm = Date.now() + DURACAO_SESSAO_MS;
  const token = gerarToken(cred.id, expiraEm);
  db.prepare('INSERT INTO sessoes (token, usuario_id, criada_em, expira_em) VALUES (?, ?, ?, ?)')
    .run(token, cred.id, agora(), expiraEm);
  // limpa sessoes vencidas de vez em quando
  db.prepare('DELETE FROM sessoes WHERE expira_em < ?').run(Date.now());
  return { token: token, usuario: buscarUsuario(db, cred.id) };
}

/**
 * Confere o token e devolve o usuario da sessao, ou null.
 */
function validarSessao(db, token) {
  const dados = lerToken(token);
  if (!dados) return null;
  if (dados.expiraEm < Date.now()) return null;
  const sessao = db.prepare('SELECT usuario_id, expira_em FROM sessoes WHERE token = ?').get(token);
  if (!sessao) return null;
  const usuario = buscarUsuario(db, sessao.usuario_id);
  if (!usuario || !usuario.ativo) return null;
  return usuario;
}

/**
 * Encerra a sessao (logout).
 */
function encerrarSessao(db, token) {
  const r = db.prepare('DELETE FROM sessoes WHERE token = ?').run(String(token || ''));
  return r.changes > 0;
}

/**
 * Quantas sessoes abertas (nao vencidas) o usuario tem.
 */
function sessoesAtivas(db, usuarioId) {
  const r = db.prepare('SELECT COUNT(*) AS n FROM sessoes WHERE usuario_id = ? AND expira_em > ?')
    .get(Number(usuarioId), Date.now());
  return Number(r.n);
}

module.exports = {
  sessoesAtivas,
  login,
  validarSessao,
  encerrarSessao,
};
