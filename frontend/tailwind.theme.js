// Tokens de diseño de Erato: un bar de jazz de noche.
// Fondo marrón-negro, tinta crema y un único acento ámbar (luz de tungsteno).
export default {
  colors: {
    ground: '#120d09',   // fondo de la sala
    surface: '#1c1510',  // paneles
    raised: '#271d16',   // paneles elevados, botones secundarios
    line: '#3d2e22',     // bordes de campos
    ink: '#f4eadb',      // texto principal
    muted: '#c4b39b',    // texto secundario (contraste AA sobre ground y surface)
    brass: {
      DEFAULT: '#f0a43a', // acento: acciones y acorde activo
      hover: '#ffb954',
      ink: '#1a1108',     // texto sobre el acento
    },
    status: {            // estado de la canción: verde, amarillo y morado pedidos por el autor
      idea: '#c9a4ff',
      progress: '#f2d14e',
      ready: '#7fd08a',
    },
    fret: '#6b5640',
    string: '#a8937a',
    nut: '#d9c8ae',
    ivory: '#efe3d0',
  },
  fontFamily: {
    display: ['"Instrument Serif"', 'Georgia', 'serif'],
    sans: ['"Hanken Grotesk"', 'system-ui', 'sans-serif'],
  },
  backgroundImage: {
    lamp: 'radial-gradient(60% 55% at 50% 0%, rgba(240,164,58,.20), rgba(240,164,58,.05) 50%, rgba(240,164,58,0) 78%)',
    spot: 'radial-gradient(50% 50% at 50% 50%, rgba(240,164,58,.13), rgba(240,164,58,0) 70%)',
  },
  keyframes: {
    roll: { from: { transform: 'translateY(0)' }, to: { transform: 'translateY(-50%)' } },
  },
  animation: {
    roll: 'roll 36s linear infinite',
  },
}
