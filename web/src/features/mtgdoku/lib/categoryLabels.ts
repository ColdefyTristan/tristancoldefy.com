/**
 * Mapping des IDs de catégories backend vers des labels français + icônes mana-font.
 *
 * IDs possibles (cf. doku_categories.py) :
 *   c=w  c=u  c=b  c=r  c=g  c=c           → couleur exacte monocolor
 *   c=wu c=wb c=ub ...                       → couleur exacte bicolor
 *   c>w  c>u  c>b  c>r  c>g               → au moins cette couleur
 *   cmc=1 … cmc=5                            → coût converti
 *   type=creature|enchantment|artifact|land|instant|sorcery|legendary
 *   pow=0 … pow=5                            → force
 *   tou=0 … tou=5                            → endurance
 *   o:"flying"|"reach"|...                   → oracle text (mot-clé ou mention)
 */

export type CategoryDisplay = {
  text: string;
  /** Classes CSS mana-font, ex: ['ms', 'ms-w'] pour chaque icône. */
  icons: string[][];
};

// ─── Couleurs ─────────────────────────────────────────────────────────────────

const COLOR_MANA: Record<string, string> = {
  w: 'ms-w', u: 'ms-u', b: 'ms-b', r: 'ms-r', g: 'ms-g', c: 'ms-c',
};

const COLOR_FR: Record<string, string> = {
  w: 'Blanc', u: 'Bleu', b: 'Noir', r: 'Rouge', g: 'Vert', c: 'Incolore',
};

// ─── Types de cartes ──────────────────────────────────────────────────────────

const TYPE_ICON: Record<string, string> = {
  creature:    'ms-creature',
  enchantment: 'ms-enchantment',
  artifact:    'ms-artifact',
  land:        'ms-land',
  instant:     'ms-instant',
  sorcery:     'ms-sorcery',
  legendary:   'ms-legendary',
};

const TYPE_FR: Record<string, string> = {
  creature:    'Créature',
  enchantment: 'Enchantement',
  artifact:    'Artefact',
  land:        'Terrain',
  instant:     'Éphémère',
  sorcery:     'Rituel',
  legendary:   'Légendaire',
};

// ─── Oracle text ──────────────────────────────────────────────────────────────

const KEYWORD_FR: Record<string, string> = {
  flying:         'Vol',
  reach:          'Portée',
  indestructible: 'Indestructible',
  trample:        'Piétinement',
  haste:          'Célérité',
  deathtouch:     'Contact mortel',
  lifelink:       'Lien vital',
};

const MENTION_FR: Record<string, string> = {
  exile:      'exil',
  graveyard:  'cimetière',
  discard:    'défausse',
  hand:       'main',
  library:    'bibliothèque',
  scry:       'scruter',
  '+1/+1':    '+1/+1',
  '-1/-1':    '-1/-1',
  token:      'jeton',
  sacrifice:  'sacrifice',
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function mana(cls: string): string[] {
  return ['ms', 'ms-cost', cls];
}

function type(cls: string): string[] {
  return ['ms', cls];
}

// ─── Lookup principal ─────────────────────────────────────────────────────────

export function getCategoryDisplay(id: string): CategoryDisplay {

  // Exact monocolor: c=w  c=u  c=b  c=r  c=g  c=c
  const mono = id.match(/^c=([wubrgc])$/);
  if (mono) {
    const c = mono[1];
    return { text: `Uniquement ${COLOR_FR[c]}`, icons: [mana(COLOR_MANA[c])] };
  }

  // Exact bicolor: c=wu  c=wb  etc.
  const bi = id.match(/^c=([wubrg])([wubrg])$/);
  if (bi) {
    const [, c1, c2] = bi;
    return {
      text: `${COLOR_FR[c1]}/${COLOR_FR[c2]}`,
      icons: [mana(COLOR_MANA[c1]), mana(COLOR_MANA[c2])],
    };
  }

  // At least color: c>w  c>u  etc.
  const atLeast = id.match(/^c>([wubrg])$/);
  if (atLeast) {
    const c = atLeast[1];
    return {
      text: `${COLOR_FR[c]} et multicolore`,
      icons: [mana(COLOR_MANA[c])],
    };
  }

  // CMC: cmc=1 … cmc=5
  const cmc = id.match(/^cmc=(\d+)$/);
  if (cmc) {
    const n = cmc[1];
    return { text: `Coût ${n}`, icons: [mana(`ms-${n}`)] };
  }

  // Card type
  const typeM = id.match(/^type=(.+)$/);
  if (typeM) {
    const t = typeM[1];
    const icon = TYPE_ICON[t];
    return { text: TYPE_FR[t] ?? t, icons: icon ? [type(icon)] : [] };
  }

  // Power: pow=0 … pow=5, pow>X, pow<X
  const pow = id.match(/^pow([=><])(\d+)$/);
  if (pow) {
    return { text: `Force ${pow[1]} ${pow[2]}`, icons: [type('ms-power')] };
  }

  // Toughness: tou=0 … tou=5, tou>X, tou<X
  const tou = id.match(/^tou([=><])(\d+)$/);
  if (tou) {
    return { text: `Endurance ${tou[1]} ${tou[2]}`, icons: [type('ms-toughness')] };
  }

  // Oracle text: o:"keyword" ou o:"mention"
  const oracle = id.match(/^o:"(.+)"$/);
  if (oracle) {
    const term = oracle[1];
    const frTerm = KEYWORD_FR[term] ?? MENTION_FR[term] ?? term;
    return { text: `mentionne «\u202f${frTerm}\u202f»`, icons: [] };
  }

  // Fallback (affiche le label brut)
  return { text: id, icons: [] };
}
