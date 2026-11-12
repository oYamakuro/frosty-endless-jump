import { createClient } from 'npm:@supabase/supabase-js@2';

const allowedOrigins = new Set([
  'https://oyamakuro.github.io',
  'http://localhost:8000',
  'http://127.0.0.1:8000',
]);
function response(data: unknown, status = 200, origin = '') {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'Access-Control-Allow-Origin': allowedOrigins.has(origin) ? origin : 'https://oyamakuro.github.io',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
    },
  });
}
const fail = (message: string, status: number, origin: string) => response({ error: message }, status, origin);
const nameRule = /^[\p{L}\p{N} ._-]{2,18}$/u;
const tokenRule = /^[a-f0-9]{48}$/;
async function hashToken(token: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}
function privilegedKey(): string {
  const secrets = Deno.env.get('SUPABASE_SECRET_KEYS');
  if (secrets) {
    try {
      const value = JSON.parse(secrets)['default'];
      if (typeof value === 'string' && value) return value;
    } catch { /* legacy key fallback */ }
  }
  return Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || '';
}
Deno.serve(async req => {
  const origin = req.headers.get('Origin') || '';
  if (req.method === 'OPTIONS') return response({}, 200, origin);
  if (origin && !allowedOrigins.has(origin)) return fail('Origin not allowed', 403, origin);
  const dbUrl = Deno.env.get('SUPABASE_URL');
  const key = privilegedKey();
  if (!dbUrl || !key) return fail('Leaderboard is not configured', 503, origin);
  const db = createClient(dbUrl, key, { auth: { persistSession: false, autoRefreshToken: false } });
  try {
    if (req.method === 'GET') {
      const { data, error, count } = await db.from('frosty_players')
        .select('name,best_score', { count: 'exact' })
        .gt('best_score', 0).order('best_score', { ascending: false })
        .order('updated_at', { ascending: true }).limit(50);
      if (error) return fail('Could not load world leaderboard', 500, origin);
      const entries = (data || []).map(row => ({ name: row.name, score: row.best_score }));
      return response({ entries, total: count || entries.length }, 200, origin);
    }
    if (req.method !== 'POST') return fail('Method not allowed', 405, origin);
    const contentLength = Number(req.headers.get('content-length') || '0');
    if (contentLength > 1024) return fail('Payload too large', 413, origin);
    const body = await req.json();
    if (!body || !tokenRule.test(String(body.token || ''))) return fail('Invalid player token', 400, origin);
    const tokenHash = await hashToken(body.token);
    if (body.action === 'register') {
      const name = String(body.name || '').trim().replace(/\s+/g, ' ');
      if (!nameRule.test(name)) return fail('Invalid player name', 400, origin);
      const { data: existing, error: findError } = await db.from('frosty_players')
        .select('id,name').eq('token_hash', tokenHash).maybeSingle();
      if (findError) return fail('Could not load profile', 500, origin);
      if (existing) {
        if (existing.name.toLowerCase() === name.toLowerCase()) return response({ ok: true, name: existing.name }, 200, origin);
        const { error } = await db.from('frosty_players').update({ name, updated_at: new Date().toISOString() })
          .eq('id', existing.id);
        if (error?.code === '23505') return fail('Player name already taken', 409, origin);
        if (error) return fail('Could not rename player', 500, origin);
        return response({ ok: true, name }, 200, origin);
      }
      const { error } = await db.from('frosty_players').insert({ name, token_hash: tokenHash });
      if (error?.code === '23505') return fail('Player name already taken', 409, origin);
      if (error) return fail('Could not create profile', 500, origin);
      return response({ ok: true, name }, 201, origin);
    }
    if (body.action === 'score') {
      const score = Number(body.score);
      if (!Number.isSafeInteger(score) || score < 0 || score > 100000) return fail('Invalid score', 400, origin);
      const { data: player, error: findError } = await db.from('frosty_players')
        .select('id,best_score,last_score_at').eq('token_hash', tokenHash).maybeSingle();
      if (findError) return fail('Could not load player', 500, origin);
      if (!player) return fail('Register player name first', 404, origin);
      if (score <= player.best_score) return response({ ok: true, best: player.best_score }, 200, origin);
      if (player.last_score_at && Date.now() - Date.parse(player.last_score_at) < 2500)
        return fail('Score submission too frequent', 429, origin);
      const { error } = await db.from('frosty_players').update({
        best_score: score, last_score_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }).eq('id', player.id).lt('best_score', score);
      if (error) return fail('Could not save score', 500, origin);
      return response({ ok: true, best: score }, 200, origin);
    }
    return fail('Unknown action', 400, origin);
  } catch {
    return fail('Invalid request', 400, origin);
  }
});
